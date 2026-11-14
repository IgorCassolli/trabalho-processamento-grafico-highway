from pathlib import Path
import time
import cv2
import numpy as np

base = Path("assets/highway")
saida = Path("resultados")
saida.mkdir(exist_ok=True)

limiar = 25

with open(base / "temporalROI.txt") as arquivo:
    inicio_aval, fim_aval = arquivo.read().split()
inicio_aval = int(inicio_aval)
fim_aval = int(fim_aval)

roi = cv2.imread(str(base / "ROI.bmp"), cv2.IMREAD_GRAYSCALE)
if roi is None:
    raise FileNotFoundError("Não foi possível abrir a ROI")

total = len(list((base / "input").glob("in*.jpg")))

frame_anterior = None
gravador = None

tp = 0
fp = 0
fn = 0

tempo_total = 0.0
serie = []

for i in range(1, total + 1):
    frame = cv2.imread(str(base / "input" / f"in{i:06d}.jpg"))
    if frame is None:
        raise FileNotFoundError(f"Não foi possível abrir o frame {i}")

    inicio = time.perf_counter()

    atual = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    atual = cv2.GaussianBlur(atual, (5, 5), 0)

    if frame_anterior is None:
        frame_anterior = atual
        continue

    diferenca = cv2.absdiff(frame_anterior, atual)

    _, movimento = cv2.threshold(diferenca, limiar, 255, cv2.THRESH_BINARY)

    movimento = cv2.medianBlur(movimento, 5)

    movimento = cv2.dilate(movimento, None, iterations=2)

    contornos, _ = cv2.findContours(
        movimento, cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)

    quantidade = 0
    for contorno in contornos:
        if cv2.contourArea(contorno) < 50:
            continue

        x, y, largura, altura = cv2.boundingRect(contorno)
        cv2.rectangle(
            frame, (x, y),
            (x + largura, y + altura),
            (0, 255, 0), 1)
        quantidade += 1

    area = np.count_nonzero(movimento)

    frame_anterior = atual

    tempo_total += time.perf_counter() - inicio

    serie.append((i, quantidade, area))

    if inicio_aval <= i <= fim_aval:
        gt = cv2.imread(str(base / "groundtruth" / f"gt{i:06d}.png"), cv2.IMREAD_GRAYSCALE)
        validos = (roi > 0) & (gt != 50) & (gt != 170) & (gt != 85)

        real = gt == 255
        previsto = movimento > 0

        tp += np.count_nonzero(previsto & real & validos)
        fp += np.count_nonzero(previsto & ~real & validos)
        fn += np.count_nonzero(~previsto & real & validos)

    if gravador is None:
        altura_video, largura_video = frame.shape[:2]
        codec = cv2.VideoWriter_fourcc(*"MJPG")
        gravador = cv2.VideoWriter(
            str(saida / "diferenca_anotado.avi"),
            codec,
            25,
            (largura_video, altura_video),
            isColor=True,
        )
    gravador.write(frame)

    # Títulos sem acento: o imshow no Windows não exibe acentos corretamente
    cv2.imshow("Deteccao de movimento", frame)
    cv2.imshow("Mascara", movimento)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

gravador.release()
cv2.destroyAllWindows()

precisao = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * precisao * recall / (precisao + recall) if (precisao + recall) > 0 else 0

tempo_medio = tempo_total / len(serie) * 1000

texto = (
    "Investigação - método sequencial (diferença de frames)\n"
    f"Parâmetros: limiar={limiar}\n\n"
    f"Resultados quantitativos (frames {inicio_aval}-{fim_aval}):\n"
    f"  Precisão = {precisao:.3f}\n"
    f"  Recall   = {recall:.3f}\n"
    f"  F1       = {f1:.3f}\n\n"
    f"Tempo de processamento: {tempo_medio:.2f} ms/frame\n"
)
print(texto)

with open(saida / "investigacao_metodo_sequencial.txt", "w", encoding="utf-8") as arquivo:
    arquivo.write(texto)

with open(saida / "diferenca_serie.csv", "w") as arquivo:
    arquivo.write("frame,n_regioes,area_pixels\n")
    for frame_i, quantidade, area in serie:
        arquivo.write(f"{frame_i},{quantidade},{area}\n")
