// a first seed for styling a notebook inside a mooc infra
function mooc_style(Jupyter) {
    $("div#header-container").hide();
    $("body.notebook_app").css("background", "red");
    
}

events.on("notebook_loaded.Notebook", function () {
    mooc_sytle(Juyter);
})
