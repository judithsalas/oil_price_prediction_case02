# =============================================================
#  Modelos: RNN simple, LSTM y GRU con la misma arquitectura
#
#  Las tres redes solo se diferencian en la capa recurrente; el resto
#  (entrada, tamaño oculto, capas, salida) es igual -> comparación justa.
#  Salida: log-rentabilidad prevista del Brent a h días (ver preproceso.py).
# =============================================================
import numpy as np
import torch
from torch import nn

TIPOS = {'rnn': nn.RNN, 'lstm': nn.LSTM, 'gru': nn.GRU}


class Recurrente(nn.Module):
    def __init__(self, tipo, n_entradas, oculto=64, capas=1, dropout=0.0):
        super().__init__()
        self.red = TIPOS[tipo](n_entradas, oculto, capas, batch_first=True,
                               dropout=dropout if capas > 1 else 0.0)
        self.dropout = nn.Dropout(dropout)    # también con 1 capa, antes de la salida
        self.salida = nn.Linear(oculto, 1)
        # Desviación típica del objetivo en train (la fija entrenar): la red
        # trabaja en escala ~1 y la salida vuelve a log-rentabilidad.
        self.register_buffer('escala', torch.ones(()))
        self._iniciar(tipo, oculto)

    def _iniciar(self, tipo, oculto):
        # Como Keras (recurrent_initializer='orthogonal', unit_forget_bias=True):
        # - W_hh ortogonal en cada puerta: norma 1, así el producto de normas
        #   de BPTT ni se desvanece ni explota al empezar.
        # - Sesgos a 0, salvo la puerta de olvido de la LSTM a 1: f = σ(1) ≈ 0,73,
        #   al principio la celda conserva la memoria en vez de borrarla.
        for nombre, p in self.red.named_parameters():
            if nombre.startswith('weight_hh'):
                for puerta in p.data.split(oculto):
                    nn.init.orthogonal_(puerta)
            elif nombre.startswith('bias'):
                nn.init.zeros_(p)
                if tipo == 'lstm' and nombre.startswith('bias_ih'):
                    p.data[oculto:2 * oculto] = 1.0   # orden de PyTorch: i, f, g, o

    def forward(self, x):                 # x: (lote, ventana, n_entradas)
        estados, _ = self.red(x)
        z = self.salida(self.dropout(estados[:, -1])).squeeze(-1)   # estado del día t
        return z * self.escala


def n_parametros(modelo):
    return sum(p.numel() for p in modelo.parameters())


def ingenuo(X):
    # "El precio futuro = el precio de hoy" -> log-rentabilidad 0
    return np.zeros(len(X), dtype=np.float32)
