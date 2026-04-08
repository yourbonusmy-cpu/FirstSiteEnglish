function updateTranslations(partId) {
  translationSelect.innerHTML = "";

  const block = Array.from(translationsBlocks)
    .find(b => b.dataset.partId === partId);

  if (!block) {
    translationSelect.innerHTML =
      '<option selected disabled>Нет перевода</option>';
    return;
  }

  const spans = block.querySelectorAll("span");
  let mainFound = false;

  spans.forEach(span => {
    const opt = document.createElement("option");
    opt.value = span.dataset.id;
    opt.textContent = span.textContent;

    if (span.dataset.isMain === "1" && !mainFound) {
      opt.selected = true;
      mainFound = true;
    }

    translationSelect.appendChild(opt);
  });

  if (!mainFound && translationSelect.options.length) {
    translationSelect.options[0].selected = true;
  }
}
