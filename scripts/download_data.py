# Descarga los datos del caso y los guarda en data/petroleo_dataset.csv
# Uso: poetry run python -m scripts.download_data
from petroleo.datos import descargar, guardar

if __name__ == '__main__':
    datos = descargar()
    guardar(datos)
    print(datos.shape)
    print(datos.tail())
