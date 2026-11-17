# =============================================================
#  Entrenamiento con parada temprana (early stopping)
#
#  Se entrena con train y, al final de cada época, se mide el error en el
#  conjunto de parada. Se guarda la mejor época y se para si en `paciencia` épocas
#  seguidas no mejora. Los mismos ajustes valen para las tres redes.
# =============================================================
import copy
import time

import numpy as np
import torch


def predecir(modelo, X):
    modelo.eval()
    with torch.no_grad():
        return modelo(torch.as_tensor(X)).numpy()


def mse(modelo, X, y):
    return float(np.mean((predecir(modelo, X) - y) ** 2))


def entrenar(modelo, train, val, epocas=50, paciencia=5, lr=1e-3, lote=64, l2=0.0):
    """Entrena `modelo` in situ y lo deja con los pesos de la mejor época.

    train, val: (X, y, ...) como los devuelve preproceso.preparar.
    l2: penalización L2 de los pesos (kernel/recurrent_regularizer de Keras).
    """
    X, y = torch.as_tensor(train[0]), torch.as_tensor(train[1])
    # Objetivo sin tendencia y en escala ~1: la red aprende y - media(y) en
    # unidades de desviación típica y predice con deriva 0. Si no, aprende la
    # subida media de 2000-2014 y la proyecta al futuro.
    media = y.mean()
    modelo.escala.fill_(float(y.std()))
    objetivo = (y - media) / modelo.escala
    opt = torch.optim.Adam(modelo.parameters(), lr=lr, weight_decay=l2)
    mejor, mejor_estado, sin_mejora = float('inf'), None, 0
    historial = {'mse_train': [], 'mse_val': []}
    inicio = time.perf_counter()

    for epoca in range(1, epocas + 1):
        modelo.train()
        for idx in torch.randperm(len(X)).split(lote):
            opt.zero_grad()
            # Huber: los días extremos pesan menos que con MSE
            perdida = torch.nn.functional.huber_loss(modelo(X[idx]) / modelo.escala,
                                                     objetivo[idx])
            perdida.backward()
            # Las RNN pueden "explotar" con gradientes grandes: se limitan
            torch.nn.utils.clip_grad_norm_(modelo.parameters(), 1.0)
            opt.step()

        # Las dos curvas con la misma métrica y sin dropout: comparables
        historial['mse_train'].append(mse(modelo, train[0], train[1]))
        error_val = mse(modelo, val[0], val[1])
        historial['mse_val'].append(error_val)
        if error_val < mejor:
            mejor, mejor_estado, sin_mejora = error_val, copy.deepcopy(modelo.state_dict()), 0
            mejor_epoca = epoca
        else:
            sin_mejora += 1
            if sin_mejora >= paciencia:
                break

    modelo.load_state_dict(mejor_estado)
    return {'mse_val': mejor, 'mse_train': historial['mse_train'][mejor_epoca - 1],
            'mejor_epoca': mejor_epoca, 'epocas': epoca,
            'segundos': time.perf_counter() - inicio, 'historial': historial}
