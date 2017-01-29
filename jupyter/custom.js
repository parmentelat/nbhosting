define([
    'base/js/namespace',
    'base/js/events'
], function(IPython, events) {
    events.on('app_initialized.NotebookApp', function() {

	console.log("custom.js: messing with menubar/toolbar");
	// not truly useful, just a test indeed
	// this is because the menubar does not exactyl stand out
	
	//// first horizontal area (including name)
	$("div#header-container").hide();
	
	//// second horizontal area (menubar)
	// top right (python2/python3..)
	$("p#kernel_indicator").hide();
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
    });

    // set this aside - from benjamin's code
    // it's kind of working but too intrusive
    // this html needs to be injected, not to replace 
    var update_metadata = function() {
	var notebook = Jupyter.notebook;
	var notebookmeta = "";
	if(notebook.metadata.notebookname)  
	    notebookmeta = notebook.metadata.notebookname;
	if(notebook.metadata.version)
	    notebookmeta+=" v"+notebook.metadata.version;
	var notebookmetadiv = '<div class="navbar-nobg"><div class="container"><div id="ipython_notebook" class="nav brand pull-left">'+notebookmeta+'</div></div></div>' ;
	$('div#header').html(notebookmetadiv);
    }
    
    events.on('notebook_loaded.Notebook', function(){
	console.log("showing notebook metadata");
	$("#maintoolbar>div>div>div:nth-child(7)").hide();
//	$('div#menubar-container').show();
//	var cells = IPython.notebook.get_cells();
//	for (var i in cells){
//	    var cell = cells[i];
//	    if (!(cell instanceof IPython.CodeCell)) {
//		cell.code_mirror.setOption('readOnly','nocursor'); 
//	    }
//	}
//	$('.text_cell').unbind('dblclick');
    });
  
});
