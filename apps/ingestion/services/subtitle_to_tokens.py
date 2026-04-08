import re
import json

def srt_to_tokens(srt_text):
    blocks = re.split(r'\n\s*\n', srt_text.strip())
    result = []

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # 00:00:06,160 --> 00:00:15,679
        time_line = lines[1]
        start_str, end_str = time_line.split(" --> ")

        def to_seconds(t: str) -> float:
            h, m, sec_ms = t.split(":")
            s, ms = sec_ms.split(",")
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000

        start = to_seconds(start_str)
        end = to_seconds(end_str)

        text = " ".join(lines[2:])

        # удаляем >> и кавычки
        text = text.replace(">>", "")
        text = text.replace('"', '')

        # токенизация по словам
        tokens = []
        for raw in re.findall(r"[A-Za-z']+", text):
            tokens.append({"raw": raw, "lemma": raw})

        result.append({
            "start": start,
            "end": end,
            "tokens": tokens
        })

    return result

if __name__ == "__main__":
    with open("s_test.srt", "r", encoding="utf-8") as f:
        srt_text = f.read()

    tokens = srt_to_tokens(srt_text)

    with open("video_name.tokens.json", "w", encoding="utf-8") as f:
        json.dump(tokens, f, ensure_ascii=False, indent=2)
