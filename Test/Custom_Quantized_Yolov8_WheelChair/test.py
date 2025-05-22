import tensorflow as tf
interpreter = tf.lite.Interpreter(model_path="wheelChair_YOLOv8-Detection-Quantized.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
print("Input:", input_details)
print("Output:", output_details)
