# =============================================================
#  Modelos: RNN simple, LSTM y GRU con la misma arquitectura
#
#  Las tres redes solo se diferencian en la capa recurrente; el resto
#  (entrada, tamaño oculto, capas, salida) es igual -> comparación justa.
#  Salida: log-rentabilidad prevista del Brent a h días (ver preproceso.py).
# =============================================================
import numpy as np
from torch import nn

TIPOS = {'rnn': nn.RNN, 'lstm': nn.LSTM, 'gru': nn.GRU}


class Recurrente(nn.Module):
    def __init__(self, tipo, n_entradas, oculto=64, capas=1, dropout=0.0):
        super().__init__()
        self.red = TIPOS[tipo](n_entradas, oculto, capas, batch_first=True,
                               dropout=dropout if capas > 1 else 0.0)
        self.salida = nn.Linear(oculto, 1)

    def forward(self, x):                 # x: (lote, ventana, n_entradas)
        estados, _ = self.red(x)
        return self.salida(estados[:, -1]).squeeze(-1)   # estado del día t


def n_parametros(modelo):
    return sum(p.numel() for p in modelo.parameters())


def ingenuo(X):
    # "El precio futuro = el precio de hoy" -> log-rentabilidad 0
    return np.zeros(len(X), dtype=np.float32)
