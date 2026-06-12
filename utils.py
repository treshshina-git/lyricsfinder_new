def split_text(text: str, size: int = 4000):
  return [
    text[i:i + size]
    for i in range(0, len(text), size)
  ]
