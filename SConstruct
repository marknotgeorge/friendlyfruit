# -*- python -*-

env = Environment()
protobuf = Builder(action="protoc -I rpc --python_out fruit/rpc $SOURCE", single_source=1,
                   prefix="../fruit/rpc/", suffix="_pb2.py", src_suffix=".proto")

env.Append(BUILDERS={"Protobuf" : protobuf})

env.Protobuf(Glob("rpc/*.proto"))
