import subprocess
import shutil

with open('.chainlit/config.toml' , 'r') as cl_f:
    toml_content = cl_f.read()
    cl_f.close()

with open('config.toml', 'r') as f:
    f.write(toml_content)
    f.close()
print(toml_content)
print('chainlit COMMAND RUN---------------')
subprocess.run(["python" ,"-m" ,"chainlit" ,"run", "app/query_index.py"])

