function clickSoundButton() {
  const som = document.getElementById("sound-click").play();
  som.currentTime = 0; // Reinicia se já estiver tocando
  som.play();
}

document.addEventListener("DOMContentLoaded", function () {
  const botoes = document.querySelectorAll(".botao-com-som");

  botoes.forEach((botao) => {
    botao.addEventListener("click", clickSoundButton);
  });
});
