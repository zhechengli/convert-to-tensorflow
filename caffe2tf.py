import argparse
import os
import sys
import tensorflow as tf
from tensorflow.python.tools.freeze_graph import freeze_graph

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Attempts to export a caffe converted model and data file produced by https://github.com/ethereon/caffe-tensorflow to a frozen tensorflow protocol buffer file")
    parser.add_argument("path_to_code_output_file", type=str, help="path to the python generated file produced by caffe-tensorflow/convert.py")
    parser.add_argument("class_name", type=str, help="Name of the class generated by caffe-tensorflow.  Check to make sure a class name was produced in the python generated file")
    parser.add_argument("input_width", type=int)
    parser.add_argument("input_height", type=int)
    parser.add_argument("input_channels", type=int)
    parser.add_argument("path_to_data_output_file", type=str, help="path to the numpy data file that caffe-tensorflow/convert.py produced")
    args = parser.parse_args()

    model_file_basename = args.class_name
    input_binary = False

    sys.path.append(os.path.dirname(args.path_to_code_output_file))
    basename, ext = os.path.splitext(os.path.basename(args.path_to_code_output_file))
    module = __import__(basename)
    print("Imported %s from" % basename)
    print(module)
    constructor = getattr(module, args.class_name)
    
    # todo pass in network dimensions
    x = tf.placeholder(tf.float32,
                       shape=[1, args.input_width, args.input_height, args.input_channels],
                       name="input")
    net = constructor({'data': x})

    sess = tf.InteractiveSession()
    sess.run(tf.global_variables_initializer())
    net.load(args.path_to_data_output_file, sess)

    model_input = x.name.replace(":0", "")
    model_output = net.get_output().name.replace(":0", "")

    width, height, channels = args.input_width, args.input_height, args.input_channels
    # END OF caffe-tensorflow/convert.py specific code ...

    graph_def = sess.graph.as_graph_def()

    tf.train.Saver().save(sess, model_file_basename + '.ckpt')
    tf.train.write_graph(sess.graph.as_graph_def(), logdir='.', name=model_file_basename + '.binary.pb', as_text=not input_binary)

    # We save out the graph to disk, and then call the const conversion routine.
    checkpoint_state_name = model_file_basename + ".ckpt.index"
    input_graph_name = model_file_basename + ".binary.pb"
    output_graph_name = model_file_basename + ".pb"

    input_graph_path = os.path.join(".", input_graph_name)
    input_saver_def_path = ""
    input_checkpoint_path = os.path.join(".", model_file_basename + '.ckpt')

    output_node_names = model_output
    restore_op_name = "save/restore_all"
    filename_tensor_name = "save/Const:0"

    output_graph_path = os.path.join('.', output_graph_name)
    clear_devices = False

    freeze_graph(input_graph_path, input_saver_def_path,
                 input_binary, input_checkpoint_path,
                 output_node_names, restore_op_name,
                 filename_tensor_name, output_graph_path,
                 clear_devices, "")

    print("Model loaded from: %s" % model_file_basename)
    print("Output written to: %s" % output_graph_path)
    print("Model input name : %s" % (model_input))
    print("Model input size : %dx%dx%d (WxHxC)" % (width, height, channels))
    print("Model output name: %s" % model_output)
