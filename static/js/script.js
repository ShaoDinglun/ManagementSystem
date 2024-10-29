document.addEventListener("DOMContentLoaded", function() {
    const roles = document.querySelectorAll(".role a");
    roles.forEach((role) => {
        role.addEventListener("mouseover", function() {
            this.style.backgroundColor = "#e6f7ff";
        });
        role.addEventListener("mouseout", function() {
            this.style.backgroundColor = "";
        });
    });
});
