const copiar = document.querySelector("#copiar");
if (copiar && navigator.clipboard) {
  copiar.hidden = false;
  copiar.addEventListener("click", async () => {
    const status = document.querySelector("#copia-status");
    try {
      await navigator.clipboard.writeText(document.querySelector("#codigo").textContent);
      status.textContent = "Código copiado.";
    } catch {
      status.textContent = "Selecione o código acima para copiá-lo.";
    }
  });
}
