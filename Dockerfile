# 使用 buildx 时，您可以在这里指定目标平台
# 但是如果您直接使用 docker build 命令，这一行应该被注释掉或删除
# FROM --platform=linux/amd64 python:3.8

# 由于您正在使用 M1 Mac，我们将使用 buildx 来构建镜像
# 因此，您不需要在 Dockerfile 中指定平台
FROM python:3.8

# 设置工作目录
WORKDIR /app

# 复制应用文件到容器中
COPY . /app

# 安装依赖，使用清华大学的 PyPI 镜像
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 暴露 Streamlit 使用的默认端口
EXPOSE 8501

# 运行 Streamlit 应用
CMD ["streamlit", "run", "webapp.py"]

# 健康检查
HEALTHCHECK --interval=5m --timeout=3s \
  CMD curl -f http://localhost:8501/ || exit 1