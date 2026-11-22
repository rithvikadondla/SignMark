"""Train and evaluate the image model for one task (TensorFlow / Keras).
Run from the project root (venv active):
    python src/train_cnn.py --task numbers --limit 500 --epochs 1     (quick smoke test, saves nothing)
    python src/train_cnn.py --task numbers
    python src/train_cnn.py --task alphabet
    python src/train_cnn.py --task phrases --finetune

Models:  alphabet, numbers -> small CNN trained from scratch (64x64 input)
         phrases           -> MobileNetV2 transfer learning (128x128 input, ImageNet weights;
                              use --no-pretrained if the weights cannot be downloaded)
The saved model contains its own rescaling, so the Flask backend feeds RAW RGB pixels (0-255)
resized to the task's input size, exactly like the training arrays.

Test data is used ONCE at the end. Validation data (taken from train earlier) is used for early
stopping and to suggest a confidence threshold. Everything printed or saved comes from this run.
Outputs: models/<task>_model.keras, models/<task>_meta.json, reports/<task>_<model>_test_* files,
         reports/<task>_<model>_training_history.png, reports/model_comparison.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluation import evaluate, plot_history, suggest_threshold
from task_data import PROJECT_ROOT, load_task

import tensorflow as tf
from tensorflow.keras import layers

MODELS = PROJECT_ROOT / "models"


def batches(x, y, batch_size, shuffle, seed):
    """tf.data pipeline that reads uint8 arrays batch by batch (low memory)."""
    rng = np.random.default_rng(seed)
    n, shape = len(x), x.shape[1:]

    def gen():
        idx = np.arange(n)
        if shuffle:
            rng.shuffle(idx)
        for i in range(0, n, batch_size):
            b = np.sort(idx[i : i + batch_size])
            yield x[b].astype(np.float32), y[b].astype(np.int64)

    sig = (tf.TensorSpec((None,) + shape, tf.float32), tf.TensorSpec((None,), tf.int64))
    return tf.data.Dataset.from_generator(gen, output_signature=sig).prefetch(
        tf.data.AUTOTUNE
    )


def augmentation():
    """Mild augmentation, active only during training."""
    return tf.keras.Sequential(
        [
            layers.RandomRotation(0.05),
            layers.RandomTranslation(0.08, 0.08),
            layers.RandomZoom(0.1),
            layers.RandomContrast(0.15),
        ],
        name="augmentation",
    )


def build_cnn(size, n_classes):
    inp = layers.Input((size, size, 3))
    x = augmentation()(inp)
    x = layers.Rescaling(1 / 255.0)(x)
    for filters in (32, 64, 128):
        for _ in range(2):
            x = layers.Conv2D(filters, 3, padding="same", use_bias=False)(x)
            x = layers.BatchNormalization()(x)
            x = layers.ReLU()(x)
        x = layers.MaxPooling2D()(x)
        x = layers.Dropout(0.25)(x)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.4)(x)
    out = layers.Dense(n_classes, activation="softmax")(x)
    return tf.keras.Model(inp, out), None


def build_mobilenet(size, n_classes, pretrained):
    base = tf.keras.applications.MobileNetV2(
        input_shape=(size, size, 3),
        include_top=False,
        weights="imagenet" if pretrained else None,
    )
    base.trainable = False
    inp = layers.Input((size, size, 3))
    x = augmentation()(inp)
    x = layers.Rescaling(1 / 127.5, offset=-1)(
        x
    )  # MobileNetV2 expects values in [-1, 1]
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    out = layers.Dense(n_classes, activation="softmax")(x)
    return tf.keras.Model(inp, out), base


def compile_model(model, lr):
    model.compile(
        optimizer=tf.keras.optimizers.Adam(lr),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )


def fit(model, train_ds, val_ds, epochs, train_count, batch_size):
    cbs = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy", patience=4, restore_best_weights=True
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss", factor=0.5, patience=2
        ),
    ]

    steps = (train_count + batch_size - 1) // batch_size

    return model.fit(
        train_ds.repeat(),
        validation_data=val_ds,
        epochs=epochs,
        steps_per_epoch=steps,
        callbacks=cbs,
        verbose=2,
        shuffle=False,
    ).history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=["alphabet", "numbers", "phrases"])
    ap.add_argument("--epochs", type=int, default=15)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument(
        "--finetune", action="store_true", help="phrases: also fine-tune the top layers"
    )
    ap.add_argument(
        "--no-pretrained", action="store_true", help="phrases: random weights"
    )
    ap.add_argument(
        "--limit",
        type=int,
        default=0,
        help="smoke test: use only N training images, save nothing",
    )
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    tf.keras.utils.set_random_seed(args.seed)
    d = load_task(args.task, limit=args.limit, seed=args.seed)
    n_classes, size = len(d["class_names"]), d["size"]
    print(
        f"{args.task}: train {len(d['x_train'])}, val {len(d['x_val'])}, test {len(d['x_test'])}, "
        f"{n_classes} classes, input {size}x{size}x3"
    )
    if args.task == "phrases":
        model, base = build_mobilenet(size, n_classes, not args.no_pretrained)
        model_name = "mobilenetv2"
        lr = 1e-3
    else:
        model, base = build_cnn(size, n_classes)
        model_name = "cnn"
        lr = 1e-3
    compile_model(model, lr)
    print("parameters:", model.count_params())

    train_ds = batches(d["x_train"], d["y_train"], args.batch_size, True, args.seed)
    val_ds = batches(d["x_val"], d["y_val"], args.batch_size, False, args.seed)
    test_ds = batches(d["x_test"], d["y_test"], args.batch_size, False, args.seed)

    t0 = time.time()
    history = fit(
        model, train_ds, val_ds, args.epochs, len(d["x_train"]), args.batch_size
    )
    if base is not None and args.finetune and not args.limit:
        print("Fine-tuning the top MobileNetV2 layers...")
        base.trainable = True
        for layer in base.layers[:-30]:
            layer.trainable = False
        for layer in base.layers:
            if isinstance(layer, layers.BatchNormalization):
                layer.trainable = False
        compile_model(model, 1e-5)
        more = fit(
            model,
            train_ds,
            val_ds,
            max(5, args.epochs // 2),
            len(d["x_train"]),
            args.batch_size,
        )
        for k, v in more.items():
            history[k] = history.get(k, []) + v
    seconds = round(time.time() - t0, 1)

    val_probs = model.predict(val_ds, verbose=0)
    val_acc = float((val_probs.argmax(1) == d["y_val"]).mean())
    threshold, thr_info = suggest_threshold(val_probs, d["y_val"])
    probs = model.predict(test_ds, verbose=0)
    pred = probs.argmax(1)
    conf = probs.max(1)
    right = pred == d["y_test"]
    print(
        f"validation accuracy {val_acc:.4f} | TEST accuracy {right.mean():.4f} | trained in {seconds}s"
    )
    if args.limit:
        print("Smoke test only: nothing saved. If this worked, run without --limit.")
        return

    MODELS.mkdir(exist_ok=True)
    model.save(MODELS / f"{args.task}_model.keras")
    extra = {
        "train_seconds": seconds,
        "parameters": int(model.count_params()),
        "validation_accuracy": val_acc,
        "epochs_run": len(history["loss"]),
        "mean_confidence_when_correct": float(conf[right].mean())
        if right.any()
        else None,
        "mean_confidence_when_wrong": float(conf[~right].mean())
        if (~right).any()
        else None,
    }
    summary = evaluate(
        args.task, model_name, d["y_test"], pred, d["class_names"], extra=extra
    )
    plot_history(args.task, model_name, history)
    meta = {
        "task": args.task,
        "model": model_name,
        "class_names": d["class_names"],
        "input_size": size,
        "input": "RGB, float or uint8 values 0-255, resized to input_size x input_size",
        "preprocessing_inside_model": True,
        "suggested_confidence_threshold": threshold,
        "threshold_chosen_on": "validation data",
        "threshold_info": thr_info,
        "test_accuracy": summary["accuracy"],
        "trained": time.strftime("%Y-%m-%d %H:%M:%S"),
        "seed": args.seed,
    }
    (MODELS / f"{args.task}_meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print(
        f"TEST macro precision {summary['precision_macro']:.4f} | macro recall "
        f"{summary['recall_macro']:.4f} | macro F1 {summary['f1_macro']:.4f}"
    )
    print(
        f"Saved models/{args.task}_model.keras, models/{args.task}_meta.json and reports/ files"
    )


if __name__ == "__main__":
    main()
