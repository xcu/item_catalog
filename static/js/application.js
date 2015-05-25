$(document).ready(function() {
    $('.categories').on('click', 'button.add', function() {
        dialogAdd.dialog( "open" );
    });

    $('.categories').on('click', 'button.remove', function() {
        dialogDelete.dialog( "open" );
    });

    $('.categoryItems').on('click', 'button.add', function() {
        dialogAdd.dialog( "open" );
    });

    $('.categoryItems').on('click', 'button.remove', function() {
        dialogDelete.dialog( "open" );
    });

    $('.item').on('click', 'button.edit', function() {
        dialogEdit.dialog( "open" );
    });

    $('.item').on('click', 'button.delete', function() {
        dialogDelete.dialog( "open" );
    });
    var dialogAdd, dialogEdit, dialogDelete, addForm, editForm;
    var name = $("#cat_name"),
        description = $("#cat_description"),
        allFields = $([]).add(name).add(description),
        tips = $(".validateTips");

    function validate(){
        return true;
        var valid = true;
        allFields.removeClass( "ui-state-error" );
        valid = valid && checkLength( name, "name", 3);
        valid = valid && checkLength( description, "description", 5);
        return valid;
    }

    function updateTips( t ) {
      tips
        .text( t )
        .addClass( "ui-state-highlight" );
      setTimeout(function() {
        tips.removeClass( "ui-state-highlight", 1500 );
      }, 500 );
    }

    function checkLength(o, n, min){
      if (o.val().length < min ) {
        o.addClass( "ui-state-error" );
        updateTips( "Length of " + n + " must be between " +
          min + "." );
        return false;
      } else {
        return true;
      }
    }

    function checkRegexp( o, regexp, n ) {
      if ( !( regexp.test( o.val() ) ) ) {
        o.addClass( "ui-state-error" );
        updateTips( n );
        return false;
      } else {
        return true;
      }
    }

    function addItem() {
        event.preventDefault();
        if (!validate()){
            return false;
        }
        $.ajax(addForm.attr('action'), {
            type: 'POST',
            //contentType: "application/json; charset=utf-8",
            dataType:'json',
            data: addForm.serialize(),
            success: function(result) {
                if (result.type_added == 'category'){
                    afterAddCategory(result.name, result.href);
                }
                else if (result.type_added == 'item'){
                    afterAddItem(result.name, result.href);
                }
            },
            error: function(result) {
                console.log(result);
            },
            complete: function(result) {
                dialogAdd.dialog( "close" );
                // undo button highlight
            },
        });
      return true;
    }

    function afterAddCategory(categoryName, categoryURL){
        var newCategory = '<li><a href="' +
                            categoryURL +
                            '">' +
                            categoryName +
                            '</a></li>';
        $('.categoryList').append($(newCategory));
    }

    function afterAddItem(itemName, itemURL){
        var newItem = '<li><a href="' +
                            itemURL +
                            '">' +
                            itemName +
                            '</a></li>';
        $('.itemList').append($(newItem));
    }

    function editItem() {
        event.preventDefault();
        $.ajax(editForm.attr('action'), {
            type: 'PUT',
            //contentType: "application/json; charset=utf-8",
            dataType:'json',
            data: editForm.serialize(),
            success: function(result) {
                itemDiv = $('.item')
                itemDiv.find('.itemName').text(result['item_name'])
                itemDiv.find('.itemDescription').text(result['item_desc'])
                console.log(result);
            },
            error: function(result) {
                console.log(result);
            },
            complete: function(result) {
                dialogEdit.dialog( "close" );
                // undo button highlight
            },
        });
      return true;
    }

    function deleteItem() {
        event.preventDefault();
        $.ajax($( "#dialog-confirm" ).attr('action'), {
            type: 'DELETE',
            dataType:'json',
            success: function(result) {
                console.log(result);
                window.location.href = result.redirect;
            },
            error: function(result) {
                console.log(result);
            },
            complete: function(result) {
                dialogDelete.dialog("close");
                // undo button highlight
            },
        });
    }

    dialogAdd = $( "#dialog-form-add" ).dialog({
        autoOpen: false,
        height: 390,
        width: 350,
        modal: true,
        buttons: {
          "Add": addItem,
          Cancel: function() {
            dialogAdd.dialog("close");
          }
        },
        close: function() {
          addForm[0].reset();
          allFields.removeClass( "ui-state-error" );
        }
      });

    dialogEdit = $( "#dialog-form" ).dialog({
      autoOpen: false,
      height: 350,
      width: 350,
      modal: true,
      buttons: {
        "Submit": editItem,
        Cancel: function() {
          dialogEdit.dialog( "close" );
        }
      },
      close: function() {
        editForm[0].reset();
      }
    });

    dialogDelete = $( "#dialog-confirm" ).dialog({
        autoOpen: false,
        resizable: false,
        height:170,
        modal: true,
        buttons: {
            "Send it to /dev/null": deleteItem,
            Cancel: function() {
                $( this ).dialog( "close" );
            }
        }
    });

    editForm = dialogEdit.find( "form" );
    addForm = dialogAdd.find( "form" );
});

//('.confirmation').on('click', 'button', function(){
//    $.ajax('confirmation.html', {
//        success: function(response) {},
//        error: function(request, errorType, errorMessage) {},
//        timeout: 3000,
//        ￼￼￼￼beforeSend: function() {
//          $('.confirmation').addClass('is-loading');
//        },
//        complete: function() {
//        ￼￼  $('.confirmation').removeClass('is-loading');
//        }
//    ￼});
//});

//var confirmation = {
//    init: function() {
//        $('.confirmation').on('click', 'button', this.loadConfirmation);
//        $('.confirmation').on('click', '.view-boarding-pass', this.showBoardingPass);
//    },
//    loadConfirmation: function() {
//        $.ajax('confirmation.html', {});
//    },
//    showBoardingPass: function(event) {}
//};
//
//$(document).ready(function() {
//  confirmation.init();
//});
// $('button').on('click', function() {
// var price = $('<p>From $399.99</p>');
// $(this).after(price);
// $(this).closest('.vacation').append(price);
//$(this).remove();