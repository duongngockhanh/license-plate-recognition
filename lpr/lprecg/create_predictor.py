import os
import sys
from paddle import inference

def str2bool(v):
    
    return v.lower() in ("true", "t", "1")

def create_predictor(model_dir, logger,use_onnx, precision=None):
    if model_dir is None:
        logger.info("not find {} model file path {}".format( model_dir))
        sys.exit(0)
    if use_onnx:
        import onnxruntime as ort
        model_file_path = model_dir
        if not os.path.exists(model_file_path):
            raise ValueError("not find model file path {}".format(
                model_file_path))
        sess = ort.InferenceSession(model_file_path)
        return sess, sess.get_inputs()[0], None, None
    else:
        file_names = ['model', 'inference']
        for file_name in file_names:
            model_file_path = '{}/{}.pdmodel'.format(model_dir, file_name)
            params_file_path = '{}/{}.pdiparams'.format(model_dir, file_name)
            if os.path.exists(model_file_path) and os.path.exists(
                    params_file_path):
                break
        if not os.path.exists(model_file_path):
            raise ValueError(
                "not find model.pdmodel or inference.pdmodel in {}".format(
                    model_dir))
        if not os.path.exists(params_file_path):
            raise ValueError(
                "not find model.pdiparams or inference.pdiparams in {}".format(
                    model_dir))

        config = inference.Config(model_file_path, params_file_path)
        config.disable_gpu()
            # cache 10 different shapes for mkldnn to avoid memory leak
        # config.set_mkldnn_cache_capacity(10)
        # config.enable_mkldnn()
        # if precision == "fp16":
        #     config.enable_mkldnn_bfloat16()
           
            
        # config.set_cpu_math_library_num_threads(10)
        # enable memory optim
        config.enable_memory_optim()
        config.disable_glog_info()
        config.delete_pass("conv_transpose_eltwiseadd_bn_fuse_pass")
        config.delete_pass("matmul_transpose_reshape_fuse_pass")
        # create predictor
        predictor = inference.create_predictor(config)
        input_names = predictor.get_input_names()
        for name in input_names:
            input_tensor = predictor.get_input_handle(name)
        output_tensors = get_output_tensors( "SVTR_LCNet", predictor)

        return predictor, input_tensor, output_tensors, config

def get_output_tensors( mode, predictor):
    output_names = predictor.get_output_names()
    output_tensors = []
    if mode == "SVTR_LCNet":
        output_name = 'softmax_0.tmp_0'
        if output_name in output_names:
            return [predictor.get_output_handle(output_name)]
        else:
            for output_name in output_names:
                output_tensor = predictor.get_output_handle(output_name)
                output_tensors.append(output_tensor)
    else:
        for output_name in output_names:
            output_tensor = predictor.get_output_handle(output_name)
            output_tensors.append(output_tensor)

    return output_tensors
