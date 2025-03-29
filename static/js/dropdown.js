function toggleDropdown() {
  document.getElementById("dropdownMenu").classList.toggle("show");
}

// Fecha o menu ao clicar fora dele
document.addEventListener("click", function (event) {
  var dropdown = document.getElementById("dropdownMenu");
  var userDiv = document.querySelector(".user");
  if (!userDiv.contains(event.target)) {
    dropdown.classList.remove("show");
  }
});


function toggleMenu() {
  document.querySelector(".box-links").classList.toggle("active");
}
