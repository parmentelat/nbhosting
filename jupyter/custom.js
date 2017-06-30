"use strict";

define([
    'base/js/namespace',
    'base/js/events',
    'notebook/js/codecell',
], function(Jupyter, events, codecell) {

    let header = "nbh's custom.js"
    
    console.log(`${header} loading`);

    //////////////////////////////////////////////////
    let hack_header_for_nbh = function(/*Jupyter*/) {

	// not truly useful, just a test indeed
	// this is because the menubar does not exactly stand out
	
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
	// run the command palette
	$("#maintoolbar>div>div>div:nth-child(7)").hide();
	// celltoolbar
	$("#maintoolbar>div>div>div:nth-child(8)").hide();

	$("#notification_trusted").hide();

	// top right (python2/python3..)
	$("p#kernel_indicator").hide();
	// move stuff from first (originally upper, then left) area
	// to second (lower, then right) area
	let last_button_group = $("div#maintoolbar-container>div:last-child");
	let ids_to_move = ['kernel_indicator', 'readonly-indicator',
			   'modal_indicator', 'notification_area'];
	for (let id of ids_to_move) {
	    last_button_group.after($(`#${id}`));
	}

	//////////
    }

    // set this aside - from benjamin's code
    // it's kind of working but too intrusive
    // this html needs to be injected, not to replace 
    let update_metadata = function(Jupyter) {
	console.log(`${header} showing notebook metadata like notebookname`);
	let notebook = Jupyter.notebook;
	let notebookmeta = "";
	if (notebook.metadata.notebookname)  
	    notebookmeta = notebook.metadata.notebookname;
	if (notebook.metadata.version)
	    notebookmeta += ` v${notebook.metadata.version}`;
	let notebookmetadiv = `<span class="metadata-bar">${notebookmeta}</span>`;
	$(notebookmetadiv).insertBefore($("#menubar"))
    }

    let inactivate_non_code_cells = function(Jupyter) {
	console.log(`${header} inactivating non-code cells`);
	let cells = Jupyter.notebook.get_cells();
	for(let cell of cells){
	    if (!(cell instanceof Jupyter.CodeCell)) {
		cell.code_mirror.setOption('readOnly', 'nocursor'); 
	    }
	}
	$('.text_cell').unbind('dblclick');
    }

    // this might sound like a good idea but needs more checking
    let redefine_enter_in_command_mode = function(Jupyter) {
	console.log(`${header} redefining Enter key in command mode`);
	Jupyter.keyboard_manager.command_shortcuts.add_shortcut(
	    'Enter', {
		help: 'nbhosting Enter key',
		handler: function(){
		    let cell = Jupyter.notebook.get_selected_cell();
		    if (cell instanceof codecell.CodeCell) {
			// code cell -> like usual Enter
			Jupyter.notebook.edit_mode()
		    } else {
			// source cell -> like shift-enter
			Jupyter.notebook.execute_cell_and_select_below()
		    }
		}
	    })
    }
	    
    // 2 minutes is a long time if you know that the server
    // can be killed at any time; observed as being 120000 on my mac
    // so it sounds like milliseconds
    let speed_up_autosave = function(Jupyter) {
	Jupyter.notebook.minimum_autosave_interval = 30000;
	console.log(`${header} speed up autosave -> ${Jupyter.notebook.minimum_autosave_interval/1000}s`)
    }

    // edxfront/views.py passes along course and student as params in the GET URL
    // so all we need to do is forge the initial URL in ipythonExercice/
    // but with the forcecopy flag
    let add_reset_and_share_buttons = function(Jupyter) {
	// stolen from jupyter-notebook/notebook/static/base/js/utils.js
	let get_url_param = function (name) {
            // get a URL parameter. I cannot believe we actually need this.
            // Based on http://stackoverflow.com/a/25359264/938949
            var match = new RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
            if (match){
		return decodeURIComponent(match[1] || '');
            }
	}
	// for reset
	let confirm_redirect = function(message, url) {
	    if (confirm(message)) {
		window.location.href = url;
	    }
	}

	// for share
	let post_share_url = function(url) {

	    $('body').append("<div id='shareDialog' title='Static notebook Created or Updated'></div>");

	    let display_dialog = function(message) {
		message = message.replace(new RegExp("\n", 'g'), "<br/>");
		$('div#shareDialog').html(message);
		$( "#shareDialog" ).dialog({
		    modal: true,
		    width: 700,
		    height: 200,
		    position:['middle', 50],
		    buttons: {
			Close: function() {
			    $( this ).dialog( "close" );
			}
		    },
		    open: function(){
			var closeBtn = $('.ui-dialog-titlebar-close');
			closeBtn.html('<span class="ui-button-icon-primary ui-icon ui-icon-closethick"></span>');
		    }
		})
	    }
	    $.ajax({
		dataType: 'json',
		url: url,
		timeout: 20000,
		success: function(data, text_status, request) {
		    // we can still successfuly receive an error....
		    let message;
		    if ('error' in data) {
			message =
			    `Could not create snapshot`
			    + `\n${data.error}`;
		    } else {
			message =
			    `To share a static version of your notebook, copy this link:`
			    + `\n${data.url}`
			    + `\n<a target='_blank' href='${data.url_path}'>try it !</a>`
			    +`\nNote that sharing the same notebook several times will overwrite the same snapshot`;
		    }
		    display_dialog(message);
		},
		error: function(request, text_status, error_thrown) {
		    console.log("post_share_url error", request);
		    console.log("post_share_url error", text_status, error_thrown);
		}
	    });
	}

	let course = get_url_param('course');
	let student = get_url_param('student');
	// window.location.pathname looks like this
	// "/35162/notebooks/w1/w1-s3-c4-fibonacci-prompt.ipynb"
	let regexp = new RegExp("^\/([0-9]+)\/notebooks\/(.*)");
	// groups 1 and 2 refer to port and notebook respectively
	let map = { port: 1, notebook: 2 };
	// parse it
	let match = regexp.exec(window.location.pathname);
	// extract notebook
	let notebook = match[map.notebook];


	// add an entry at the end of the file submenu
	$("#file_menu").append(
	    `<li class="divider"></li>`);

	let reset_url = `/ipythonExercice/${course}/${notebook}/${student}?forcecopy=true`;
	$('#file_menu').append(
	    `<li id="reset_from_origin"><a href="#">Reset from original</a></li>`);
	$('#reset_from_origin').click(function() {
	    confirm_redirect("Are you sure to reset your notebok to the original version ?"
			     + "\n(all your changes will be lost)",
			     reset_url);
	})
	
	let share_url = `/ipythonShare/${course}/${notebook}/${student}`;
	$('#file_menu').append(
	    `<li id="share_static_version"><a href="#">Share static version</a></li>`);
	$('#share_static_version').click(function() {
	    post_share_url(share_url);
	})
    }
    
    // run the parts
    hack_header_for_nbh(Jupyter);
    update_metadata(Jupyter);
    inactivate_non_code_cells(Jupyter);
    redefine_enter_in_command_mode(Jupyter);
    add_reset_and_share_buttons(Jupyter);
    speed_up_autosave(Jupyter);

})
