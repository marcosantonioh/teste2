// Função para alternar a visibilidade do dropdown
function toggleDropdown() {
    const dropdownMenu = document.querySelector('.dropdown-menu');
    dropdownMenu.classList.toggle('show');
}

// Fecha o dropdown se clicar fora da área do usuário
document.addEventListener('click', function(event) {
    const userDropdown = document.querySelector('.user-dropdown');
    const dropdownMenu = document.querySelector('.dropdown-menu');
    if (!userDropdown.contains(event.target)) {
        dropdownMenu.classList.remove('show');
    }
});
