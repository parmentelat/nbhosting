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

	// hide all dividers
	$("#menubar .divider").hide();

	// 'File'
	$("#new_notebook").hide();
	$("#open_notebook").hide();
	$("#copy_notebook").hide();
	$("#rename_notebook").hide();
	//keep this one: $("#restore_checkpoint").hide();
	$("#trust_notebook").hide();
	$("#kill_and_exit").hide();
	//// missing
	// Share static version
	// Reset from Origin
	
	// 'Edit' -> hide whole submenu
	$("div#menubar>div>div>div>ul.nav>li:nth-child(2)").hide();

	// View -> hide whole submenu
	$("div#menubar>div>div>div>ul.nav>li:nth-child(3)").hide();

	// Insert : is fine

	// Cell
	$("#change_cell_type").hide();
	
	// Widgets -> hide whole submenu
	// note that for this to actually work I had to do this:
	// jupyter nbextension disable jupyter-js-widgets/extension
	// otherwise this submenu entry is reactivated
	$("div#menubar>div>div>div>ul.nav>li:nth-child(7)").hide();

	// Help -> hide whole submenu
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
	$("p#kernel_indicator").hide();
	// move stuff from first (originally upper, then left) area
	// to second (lower, then right) area
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
    var update_metadata = function(Jupyter) {
	console.log("showing notebook metadata");
	var notebook = Jupyter.notebook;
	var notebookmeta = "";
	if(notebook.metadata.notebookname)  
	    notebookmeta = notebook.metadata.notebookname;
	if(notebook.metadata.version)
	    notebookmeta+=" v"+notebook.metadata.version;
	var notebookmetadiv = '<span class="metadata-bar">'
	    + notebookmeta + '</span>' ;
	$(notebookmetadiv).insertBefore($("#menubar"))
    }

    var inactivate_non_code_cells = function(Jupyter) {
	console.log("custom.js : inactivating non-code cells");
	var cells = Jupyter.notebook.get_cells();
	for(var i in cells){
	    var cell = cells[i];
	    if (!(cell instanceof Jupyter.CodeCell)) {
		cell.code_mirror.setOption('readOnly', 'nocursor'); 
	    }
	}
	$('.text_cell').unbind('dblclick');
    }

    // 2 minutes is a long time if you know that the server
    // can be killed at any time; observed as being 120000 on my mac
    // so it sounds like milliseconds
    var speed_up_autosave = function(Jupyter) {
	IPython.notebook.minimum_autosave_interval = 20000;
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
	update_metadata(Jupyter);
	inactivate_non_code_cells(Jupyter);
	speed_up_autosave(Jupyter);
//	redefine_enter_in_command_mode(Jupyter);
	
	//////////
	console.log("custom.js for mooc embedding: exiting notebook_loaded");
    });
  
});
