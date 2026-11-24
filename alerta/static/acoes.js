const copiar = document.querySelector("#copiar");
const foto = document.querySelector('input[name="foto"]');
if (foto) {
  foto.addEventListener("change", () => {
    const grande = foto.files[0]?.size > 5 * 1024 * 1024;
    const mensagem = grande ? "O PNG deve ter até 5 MB. Escolha uma foto menor." : "";
    foto.setCustomValidity(mensagem);
    document.querySelector("#erro-foto").textContent = mensagem;
  });
}
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
