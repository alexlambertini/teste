// Seleciona todos os botões de menu
document.querySelectorAll(".menu-button").forEach((button) => {
  button.addEventListener("click", function (event) {
    // Fecha todos os menus antes de abrir o correto
    document.querySelectorAll(".menu-popup").forEach((menu) => {
      menu.style.display = "none";
    });

    // Exibe o menu associado a este botão
    const menu = this.nextElementSibling; // O próximo elemento irmão é o menu
    if (menu && menu.classList.contains("menu-popup")) {
      menu.style.display = "block";
    }

    event.stopPropagation(); // Evita que o clique feche imediatamente
  });
});

// Fecha qualquer menu ao clicar fora
document.addEventListener("click", function () {
  document.querySelectorAll(".menu-popup").forEach((menu) => {
    menu.style.display = "none";
  });
});

// Funções de ação
function editar() {
  alert("Editar item!");
}

function imprimirSegundaVia() {
  alert("Imprimindo segunda via...");
}
