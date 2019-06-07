"use strict";

define([
    'base/js/namespace',
    'base/js/events',
    'base/js/dialog',
    'base/js/promises',
    'notebook/js/codecell',
    'notebook/js/promises',
], function(Jupyter, events, dialog, base_promises, codecell, nb_promises) {

    let hello = "nbh's custom.js"

    console.log(`${hello} loading`);

    //////////////////////////////////////////////////
    // see also custom.css that does most of the hiding
    let hack_header_for_nbh = function(/*Jupyter*/) {

	    // hide all dividers
        // don't do this in CSS as we have our own dividers come in later on
        $("#menubar .divider").hide();

        // rephrase the 'checkpoint' thing that is confusing
        $("#save_checkpoint>a").html("Save");

        // move stuff from first (originally upper, then left) area
        // to second (lower, then right) area
        let last_button_group = $("div#maintoolbar-container>div:last-child");
        let ids_to_move = ['kernel_indicator', 'readonly-indicator',
        		           'modal_indicator', 'notification_area'];
        for (let id of ids_to_move) {
            last_button_group.after($(`#${id}`));
        }
    }

    // display title and version
    let show_metadata_in_header = function(Jupyter) {
    	console.log(`${hello} showing notebook metadata like notebookname`);
    	let notebook = Jupyter.notebook;
    	let title = notebook.metadata.notebookname || "Untitled";
    	let version = notebook.metadata.version || "0.0";
    	let notebookmeta = `${title}<span id="metaversion">v${version}</span>`;
    	let notebookmetadiv =
    	    `<div id="metaarea" class="navbar">${notebookmeta}</div>`;
    	$(notebookmetadiv).insertBefore($("#menubar"))
    }

    let inactivate_non_code_cells = function(Jupyter) {
    	console.log(`${hello} inactivating non-code cells`);
    	let cells = Jupyter.notebook.get_cells();
    	for (let cell of cells){
    	    if (!(cell instanceof Jupyter.CodeCell)) {
        		cell.code_mirror.setOption('readOnly', 'nocursor');
    	    }
    	}
    	$('.text_cell').unbind('dblclick');
    }

    // this might sound like a good idea but needs more checking
    let redefine_enter_in_command_mode = function(Jupyter) {
    	console.log(`${hello} redefining Enter key in command mode`);
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
            }
        )
    }

    // 2 minutes is a long time if you know that the server
    // can be killed at any time; observed as being 120000 on my mac
    // so it sounds like milliseconds
    let speed_up_autosave = function(Jupyter) {
    	Jupyter.notebook.minimum_autosave_interval = 20000;
        let seconds = Jupyter.notebook.minimum_autosave_interval/1000;
    	console.log(`${hello} speed up autosave -> ${seconds}s`)
    }

    // edxfront/views.py passes along course and student as params in the GET URL
    // so all we need to do is forge the initial URL in ipythonExercice/
    // but with the forcecopy flag
    let add_reset_and_share_buttons = function(Jupyter) {
    	// stolen from jupyter-notebook/notebook/static/base/js/utils.js
    	let get_url_param = function (name) {
            // get a URL parameter. I cannot believe we actually need this.
            // Based on http://stackoverflow.com/a/25359264/938949
            let match = new RegExp('[?&]' + name + '=([^&]*)')
                            .exec(window.location.search);
            if (match){
        		return decodeURIComponent(match[1] || '');
            }
    	}

    	// stolen from
        // https://hackernoon.com/copying-text-to-clipboard-with-javascript-df4d4988697f

        function copyToClipboard(str) {
          const el = document.createElement('textarea');  // Create a <textarea> element
          el.value = str;                                 // Set its value to the string that you want copied
          el.setAttribute('readonly', '');                // Make it readonly to be tamper-proof
          el.style.position = 'absolute';
          el.style.left = '-9999px';                      // Move outside the screen to make it invisible
          document.body.appendChild(el);                  // Append the <textarea> element to the HTML document
          const selected =
            document.getSelection().rangeCount > 0        // Check if there is any content selected previously
              ? document.getSelection().getRangeAt(0)     // Store selection if found
              : false;                                    // Mark as false to know no selection existed before
          el.select();                                    // Select the <textarea> content
          document.execCommand('copy');                   // Copy - only works as a result of a user action (e.g. click events)
          document.body.removeChild(el);                  // Remove the <textarea> element
          if (selected) {                                 // If a selection existed before copying
            document.getSelection().removeAllRanges();    // Unselect everything on the HTML document
            document.getSelection().addRange(selected);   // Restore the original selection
          }
        };



    	// for reset
    	//
    	// NOTE. in a first implementation I naively tried to
    	// avoid creating a modal - i.e. avoid to call
    	// dialog.modal(options) - several times
    	// this however resulted in the buttons
    	// being primarily inactive the second time and on
    	//
    	let confirm_redirect = function(message, url) {
    	    // replace newlines with <br/>
    	    message = message.replace(new RegExp("\n", 'g'), "<br/>");
    	    // create dialog if not yet present
    	    dialog.modal({
        		title: "Confirm reset to original",
        		body: message,
        		sanitize: false,
        		keyboard: true,
        		buttons: {
        		    Cancel: {
            			click: function() {
            			    $(this).dialog('close');
            			}
        		    },
        		    'Reset to Original': {
                        class: 'btn-danger save-confirm-btn',
		                click: function() {
        			        window.location.href = url;
            			}
        		    }
        		}
    	    })
    	}


    	// for share
    	//
    	let post_share_url = function(url) {

    	    let display_share_url = function(message) {
        		message = message.replace(new RegExp("\n", 'g'), "<br/>");
        		// create dialog if not yet present
        		dialog.modal({
        		    title: 'Static notebook created (or updated)',
        		    body: message,
        		    sanitize: false,
        		    keyboard: true,
        		    buttons: {
    			        'Copy To Clipboard': {
	                        id: 'copy-to-clipboard',
    			            class: 'btn-info',
    			            click: function() {
                                let url = $('#share-url').text();
    				            copyToClipboard(url);
    			            }
    			        },
                        Close: function() {
    			            $(this).dialog(`close`);
		                }
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
        			    message = `Could not create snapshot` + `\n${data.error}`;
    		        } else {
        			    message =
`<p class='nbh-dialog'>To share a static version of your notebook, copy this link:`
+ `<a id="try-share-url" target='_blank' href='${data.url_path}'>Try the link</a></p>`
+ `<span id="share-url">${data.url}</span>`
+ `</div>`
+`<p class='nbh-dialog'>Note that sharing the same notebook several times overwrites the same snapshot</p>`;
        		    }
        		    display_share_url(message);
        		},
		        error: function(request, text_status, error_thrown) {
        		    console.log(`post_share_url - ajax returns status=<${text_status}>`
        				+ ` and error_thrown=<${error_thrown}>`);
		            // debugging only // console.log(request);
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
    	let notebook;
    	try {
    	    let match = regexp.exec(window.location.pathname);
    	    // extract notebook
    	    notebook = match[map.notebook];
    	} catch(e) {
    	    notebook = "works-only-under-nbhosting";
    	}


    	////////// add entries at the end of the 'file' menu

    	$("#file_menu").append(`<li class="divider"></li>`);

    	let reset_url =
            `/ipythonExercice/${course}/${notebook}/${student}?forcecopy=true`;
    	$('#file_menu').append(
    	    `<li id="reset_from_origin"><a href="#">Reset to Original</a></li>`);
    	$('#reset_from_origin').click(function() {
    	    confirm_redirect(`<p class="nbh-dialog">Are you sure to reset your notebook to the original version ?`
    			     + `<br/>(all your changes will be lost)</p>`,
    			     reset_url);
    	})

    	let share_url = `/ipythonShare/${course}/${notebook}/${student}`;
    	$('#file_menu').append(
    	    `<li id="share_static_version"><a href="#">Share Static Version</a></li>`);
    	$('#share_static_version').click(function() {
    	    post_share_url(share_url);
    	})
    }

    // the promises thingies are described in
    // https://github.com/jupyter/notebook/issues/2403
    // https://github.com/jupyter/notebook/pull/2719

    // run the parts in a promise
    base_promises.app_initialized.then(function(appname) {
        //console.log(`base_promises sent appname=${appname}`);
        if (appname === 'NotebookApp') {
            hack_header_for_nbh(Jupyter);
            inactivate_non_code_cells(Jupyter);
            redefine_enter_in_command_mode(Jupyter);
            add_reset_and_share_buttons(Jupyter);
            speed_up_autosave(Jupyter);
        }
    })
    nb_promises.notebook_loaded.then(function(appname){
        //console.log(`nb_promises sent appname=${appname}`);
        show_metadata_in_header(Jupyter);
    })
})

