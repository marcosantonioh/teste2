var dropdown = document.getElementById("dropdownMenu");
var userDiv = document.querySelector(".user");

function toggleDropdown() {
  dropdown.classList.toggle("show");
}

// Fecha o menu ao clicar numa opção (evita ação duplicada entre o link e o document click)
document.querySelector(".dropdown-menu").addEventListener("click", function (event) {
  event.stopPropagation();
  dropdown.classList.remove("show");
});

// Fecha o menu ao clicar fora dele
document.addEventListener("click", function (event) {
  if (!userDiv.contains(event.target)) {
    dropdown.classList.remove("show");
  }
});


function toggleMenu() {
  document.querySelector(".box-links").classList.toggle("active");
}
