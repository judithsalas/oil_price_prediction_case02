# Space de Hugging Face (tipo Docker): sirve la app en el puerto 7860.
FROM python:3.12-slim

WORKDIR /home/user/app
COPY app/requirements.txt app/requirements.txt
RUN pip install --no-cache-dir torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r app/requirements.txt

COPY configs configs
COPY petroleo petroleo
COPY scripts scripts
COPY app app
COPY models/final models/final
COPY docs/resultados/comparativa.csv docs/resultados/intervalos.csv docs/resultados/

# Hugging Face ejecuta con el usuario 1000; necesita escribir data/ y models/app/
RUN useradd -m -u 1000 user && chown -R user /home/user/app
USER user
EXPOSE 7860
CMD ["uvicorn", "app.servidor:app", "--host", "0.0.0.0", "--port", "7860"]
