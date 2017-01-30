define([
    'base/js/namespace',
    'base/js/events'
], function(Jupyter, events) {

    //////////////////////////////////////////////////
    events.on('app_initialized.NotebookApp', function() {

	console.log("custom.js for mooc embedding: entering app_initialized");
	// not truly useful, just a test indeed
	// this is because the menubar does not exactyl stand out
	
	//// first horizontal area (including name)
	$("div#header-container").hide();
	
	//// second horizontal area (menubar)
	// hide menu entries

	// 'Edit'
	$("div#menubar>div>div>div>ul.nav>li:nth-child(2)").hide();
	// View
	$("div#menubar>div>div>div>ul.nav>li:nth-child(3)").hide();
	// Widgets
	$("div#menubar>div>div>div>ul.nav>li:nth-child(7)").hide();
	// Help
	$("div#menubar>div>div>div>ul.nav>li:nth-child(8)").hide();
	
	//// third horizontal area (toolbar)
	$("div#move_up_down").hide();
	// cell type (markdown, code, etc..)
	$("select#cell_type").hide();
	// "run the command palette"
	$("#maintoolbar>div>div>div:nth-child(7)").hide();
	// celltoolbar
	$("#maintoolbar>div>div>div:nth-child(8)").hide();

	// top right (python2/python3..)
	//$("p#kernel_indicator").hide();
	var last_button_group = $("div#maintoolbar-container>div:last-child");
	var ids_to_move = ['kernel_indicator', 'readonly-indicator',
			   'modal_indicator', 'notification_area'];
	for (i in ids_to_move) {
	    var id=ids_to_move[i];
	    last_button_group.after($("#"+id));
	}
	    
	

	//////////
	console.log("custom.js for mooc embedding: exiting app_initialized");
    });

    // set this aside - from benjamin's code
    // it's kind of working but too intrusive
    // this html needs to be injected, not to replace 
    var update_metadata = function() {
	console.log("showing notebook metadata");
	var notebook = Jupyter.notebook;
	var notebookmeta = "";
	if(notebook.metadata.notebookname)  
	    notebookmeta = notebook.metadata.notebookname;
	if(notebook.metadata.version)
	    notebookmeta+=" v"+notebook.metadata.version;
	var notebookmetadiv = '<div class="navbar-nobg"><div class="container">'
	    + '<div id="ipython_notebook" class="nav brand pull-left">'
	    + notebookmeta + '</div></div></div>' ;
	$('div#header').html(notebookmetadiv);
    }

    var inactivate_non_code_cells = function(Jupyter) {
	console.log("custom.js : inactivating non-code cells");
	var cells = Jupyter.notebook.get_cells();
	for(var i in cells){
	    var cell = cells[i];
	    if (!(cell instanceof IPython.CodeCell)) {
		cell.code_mirror.setOption('readOnly', 'nocursor'); 
	    }
	}
	$('.text_cell').unbind('dblclick');
    }

    // this might sound like a good idea but needs more checking
    var redefine_enter_in_command_mode = function(Jupyter) {
	console.log("redefining the Enter key in command mode");
	Jupyter.keyboard_manager.command_shortcuts.add_shortcut(
	    'Enter', "jupyter-notebook:run-cell-and-select-next")
    }
    
    //////////////////////////////////////////////////
    events.on('notebook_loaded.Notebook', function(){
	console.log("custom.js for mooc embedding: entering notebook_loaded");
	$('body.notebook_app').show();
	inactivate_non_code_cells(Jupyter);
//	redefine_enter_in_command_mode(Jupyter);
	
	//////////
	console.log("custom.js for mooc embedding: exiting notebook_loaded");
    });
  
});
