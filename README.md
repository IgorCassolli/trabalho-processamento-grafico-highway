# Trabalho GB — Tema 3: Detecção de movimento em videomonitoramento

## Base de dados

**CDnet 2014 — Change Detection Benchmark**, categoria **Baseline**, sequência **Highway**.

- 1.700 frames de uma rodovia filmada por uma câmera fixa (320x240).
- `assets/highway/input/`: frames de entrada (`in000001.jpg` a `in001700.jpg`).
- `assets/highway/groundtruth/`: máscaras de referência (`gt000001.png` a `gt001700.png`).
- `assets/highway/ROI.bmp`: região espacial de interesse.
- `assets/highway/temporalROI.txt`: intervalo de avaliação (frames 470 a 1700).

Rótulos das máscaras de referência:

| Valor | Significado | Tratamento |
|---|---|---|
| 0 | fundo | entra na avaliação |
| 255 | movimento | entra na avaliação |
| 50 | sombra | ignorado |
| 170 | região desconhecida | ignorado |
| 85 | fora da região de interesse | ignorado |

Fonte: https://changedetection.vitalab.usherbrooke.ca/dataset2014/

## Como rodar

1. Instale as dependências:
   ```
   pip install opencv-python numpy
   ```
2. Coloque a base em `assets/highway/`, como descrito acima.
3. Abra um terminal **dentro da pasta `TrabalhoGB`** (os caminhos são relativos, como nas aulas) e execute:
   ```
   python main.py
   ```
   O `main.py` chama os dois métodos, um depois do outro: primeiro o sequencial (`metodo_sequencial.py`) e depois o de fundo adaptativo (`metodo_fundo_adaptativo.py`, ainda por fazer).
4. Cada método abre duas janelas, uma com o vídeo e as caixas e outra com a máscara de movimento. Pressione `q` para passar para o próximo método (ou encerrar) antes do fim.

## Método sequencial: diferença entre frames consecutivos

A ideia: o que se move entre um frame e o seguinte é a diferença entre os dois. A câmera é fixa, então o que não se mexe (pista, céu, árvores) fica quase igual e a diferença dá perto de zero. Onde passou um carro, a intensidade muda e a diferença sobe.

Passo a passo, para cada frame, na ordem temporal:

1. **Leitura** do frame colorido (`in000001.jpg`, `in000002.jpg`, ...).
2. **Cinza e desfoque Gaussiano 5x5** (`cvtColor` e `GaussianBlur`). Para detectar mudança basta a intensidade, e o desfoque evita que o ruído do sensor e da compressão JPEG seja confundido com movimento.
3. **Diferença** `|frame atual − frame anterior|` pixel a pixel (`absdiff`). O primeiro frame não tem anterior, então é só guardado.
4. **Limiarização** (`threshold`, limiar 25): diferença maior que 25 vira branco (movimento), o resto vira preto. Essa é a **máscara binária**.
5. **Limpeza da máscara**: filtro da mediana 5x5 (`medianBlur`) remove pontinhos isolados de ruído, e dilatação com 2 iterações (`dilate`) preenche buracos e une pedaços do mesmo carro.
6. **Regiões**: `findContours` acha cada mancha branca e `boundingRect` calcula a caixa em volta. Regiões com menos de 50 pixels são descartadas.
7. **Série temporal**: por frame, guarda o número de regiões e a área do movimento (quantidade de pixels brancos da máscara).
8. **Avaliação** com a máscara de referência, só nos frames de 470 a 1700 e só nos pixels válidos (rótulos 0 e 255, dentro da ROI). Conta acertos de movimento (TP), falsos alarmes (FP) e movimentos perdidos (FN), e calcula:
   - **Precisão**: dos pixels detectados, quantos eram movimento de verdade.
   - **Recall**: dos pixels de movimento reais, quantos foram detectados.
   - **F1**: média harmônica dos dois.
9. **Tempo**: mede só o processamento (sem a leitura do disco) e dá a média em ms por frame.

Limitação conhecida: por comparar só dois frames, o método pega bem as bordas dos carros, mas o interior de um carro de cor uniforme quase não muda e fica de fora. Um carro parado também some, porque não há diferença entre os frames.

## Saídas (pasta `resultados/`)

| Arquivo | Conteúdo |
|---|---|
| `diferenca_anotado.avi` | vídeo com as caixas desenhadas |
| `diferenca_serie.csv` | frame, número de regiões e área do movimento |
| `investigacao_metodo_sequencial.txt` | precisão, recall, F1 e tempo médio por frame |

## Método de fundo adaptativo (a fazer)

_Lacuna para a segunda parte, em `metodo_fundo_adaptativo.py`._

**Ideia:** em vez de comparar com o frame anterior, manter um **modelo do fundo** da cena e atualizá-lo aos poucos a cada frame (por exemplo `fundo = (1 − alfa) * fundo + alfa * frame`, ou `cv2.accumulateWeighted`). O movimento é o que difere do fundo.

**Para a comparação ser justa, precisa seguir o mesmo padrão do sequencial:**

- Mesmo pré-processamento (cinza e Gaussiano 5x5) e mesma limpeza da máscara (mediana 5x5 e dilatação com 2 iterações), mudando só a forma de obter a máscara.
- Mesma extração de regiões (contornos, caixas, área mínima de 50 pixels).
- Mesma avaliação: frames 470 a 1700, ignorando os rótulos 50, 170 e 85, com precisão, recall e F1.
- Mesma medição de tempo (só o processamento, em ms por frame).
- Mesmas saídas, com o nome do método no lugar de `diferenca`:
  - `resultados/fundo_anotado.avi`
  - `resultados/fundo_serie.csv`
  - `resultados/investigacao_metodo_fundo_adaptativo.txt`
- O fundo precisa ser atualizado desde o frame 1 (para aprender a cena), mesmo que a avaliação só comece no 470.

**Valores a definir e registrar:** limiar, taxa de aprendizado (`alfa`) e se a atualização do fundo é seletiva (só onde não há movimento) ou em toda a imagem.

**Comparação final:** tabela com precisão, recall, F1 e ms/frame dos dois métodos, e discussão de onde cada um funciona e onde falha.

| Método | Precisão | Recall | F1 | ms/frame |
|---|---|---|---|---|
| Diferença de frames | _ver `investigacao_metodo_sequencial.txt`_ | | | |
| Fundo adaptativo | _a preencher_ | | | |

## Arquivos

- `main.py`: ponto de entrada, chama os dois métodos.
- `metodo_sequencial.py`: diferença entre frames.
- `metodo_fundo_adaptativo.py`: fundo adaptativo (a criar).

## Referências

- Wang et al., *CDnet 2014: An Expanded Change Detection Benchmark Dataset*, CVPRW 2014.
