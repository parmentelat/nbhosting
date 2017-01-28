define([
  'base/js/namespace',
  'base/js/events'
], function(IPython, events) {
   events.on('app_initialized.NotebookApp', function() {
    $("div#header-container").hide();
    $("body.notebook_app").css("border-width", "2px");
   });
});
