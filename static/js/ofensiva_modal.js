(() => {
  const modal = document.getElementById("modalOfensiva");
  const botoesAbrir = document.querySelectorAll("[data-abrir-modal-ofensiva]");
  const botaoFechar = modal?.querySelector("[data-fechar-modal-ofensiva]");

  if (!modal || !botoesAbrir.length || !botaoFechar) return;

  const abrir = () => {
    modal.hidden = false;
    document.body.classList.add("modal-ofensiva-aberta");
    botaoFechar.focus();
  };

  const fechar = () => {
    modal.hidden = true;
    document.body.classList.remove("modal-ofensiva-aberta");
  };

  botoesAbrir.forEach((botao) => botao.addEventListener("click", abrir));
  botaoFechar.addEventListener("click", fechar);
  modal.addEventListener("click", (evento) => {
    if (evento.target === modal) fechar();
  });
  document.addEventListener("keydown", (evento) => {
    if (evento.key === "Escape" && !modal.hidden) fechar();
  });
})();
