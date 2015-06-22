
// class to validate forms. It checks that selected fields are longer than 3 chars
function Validator(fields) {
    var validator = this;
    this.fields = fields;
    this.allFields = function(){
        var toRet = $([]);
        for (var k in this.fields) {
            toRet.add(this.fields[k]);
        }
        return toRet;
    };
    this.tips = $(".validateTips");
    this.validate = function(){
        var valid = true;
        this.allFields().removeClass("ui-state-error");
        for (var k in this.fields){
            var v = this.fields[k];
            valid = valid && this.checkLength(v, k, 3);
        }
        return valid;
    };
    this.addError = function(field, message){
        field.addClass("ui-state-error");
        this.updateTips(message);
    };
    this.resetErrors = function(){
        for (var k in this.fields) {
            this.fields[k].removeClass("ui-state-error");
        }
        this.updateTips("");
    }
    this.updateTips = function(t) {
        this.tips.text(t).addClass("ui-state-highlight");
        setTimeout(function() {
            validator.tips.removeClass("ui-state-highlight", 1500);
        }, 500 );
    };
    this.checkLength = function(o, n, min){
        if (o.val() == "") return true; // has not changed
        if (o.val().length < min) {
            this.addError(o, "Length of " + n + " must be at least " + min + ".");
            return false;
        }
        return true;
    };
};

// base class for dialogs and their associated forms
function DialogWithField(validator, dialog, afterSuccessFunction, requestType) {
    var dialogWithField = this;
    this.dialog = dialog;
    this.form = this.dialog.find("form");
    this.validator = validator;
    this.afterSuccessFunction = afterSuccessFunction;
    this.requestType = requestType;
    this.onsubmit = function() {
        event.preventDefault();
        if (!this.validator.validate()){
            return false;
        }
        $.ajax(this.form.attr('action'), {
            type: this.requestType,
            dataType:'json',
            data: this.form.serialize(),
            success: function(result) {
                dialogWithField.afterSuccessFunction(result);
                dialogWithField.dialog.dialog("close");
            },
            error: function(result) {
                field = dialogWithField.validator.fields['name'];
                dialogWithField.validator.addError(field, result.responseJSON);
            },
        });
      return true;
    }
}

$(document).ready(function() {
    // delete items doesn't really match in the base class :(
    function deleteItem() {
        event.preventDefault();
        data = {"token": $(".removeDialog").find(".token").text()}
        $.ajax($( "#dialog-confirm" ).attr('action'), {
            type: 'DELETE',
            dataType:'json',
            data: data,
            success: function(result) {
                console.log(result);
                window.location.href = result.redirect;
            },
            error: function(result, err) {
                console.log(result);
            },
        });
    }
    var dialogDelete = $( "#dialog-confirm" ).dialog({
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

    // item related
    var itemValidator = new Validator({name: $("#item_name"), description: $("#item_description")});
    var addItemDialog = $( "#dialog-form-addItem" ).dialog({
        autoOpen: false,
        height: 440,
        width: 350,
        modal: true,
        buttons: {
            "Add": function() { addItemHandler.onsubmit(); },
            Cancel: function() { addItemHandler.dialog.dialog("close"); },
        },
        close: function() {
            addItemHandler.form[0].reset();
            addCategoryHandler.validator.resetErrors();
        }
    });
    function afterAddItem(result){
        var itemName = result.name,
            itemURL = result.href,
            itemImage = result.image,
            categoryName = result.category_name,
            categoryURL = result.category_url,
            newItem = '<div class="col-md-6 text-center oneItemThumbnail">' +
                      '<a href="' + itemURL + '">' + itemName + '</a>' +
                      '<a href="' + categoryURL + '"> (' + categoryName + ')</a>' +
                      '<img class="img-thumbnail" src="' + itemImage + '" alt="' + itemName + '"></div>';
        $('.itemList').append($(newItem));
        var numberOfItems = $("#numberOfItems").text();
        var regex = new RegExp("[0-9]+");
        var match = regex.exec(numberOfItems);
        $("#numberOfItems").text(numberOfItems.replace(match[0], parseInt(match[0]) + 1));
    }
    var addItemHandler = new DialogWithField(
        itemValidator,
        addItemDialog,
        afterAddItem,
        'POST');

    var editItemDialog = $( "#dialog-form-editItem" ).dialog({
        autoOpen: false,
        height: 440,
        width: 350,
        modal: true,
        buttons: {
            "Submit": function() { editItemHandler.onsubmit(); },
             Cancel: function() { editItemHandler.dialog.dialog("close"); },
        },
        close: function() {
            editItemHandler.form[0].reset();
        }
    });
    function afterEditItem(result){
        itemDiv = $('.item');
        itemDiv.find('.itemName').text(result['item_name']);
        itemDiv.find('.itemDescription').text(result['item_desc']);
        itemDiv.find('.itemImage').find('img').attr('src', result['item_image']);
        console.log(result);
    }
    var editItemHandler = new DialogWithField(itemValidator, editItemDialog, afterEditItem, 'PUT');

    // category related
    var addCategoryDialog = $("#dialog-form-addCategory").dialog({
        autoOpen: false,
        height: 240,
        width: 350,
        modal: true,
        buttons: {
            "Add": function() { addCategoryHandler.onsubmit(); },
            Cancel: function() { addCategoryHandler.dialog.dialog("close"); },
        },
        close: function() {
            addCategoryHandler.form[0].reset();
            addCategoryHandler.validator.resetErrors();
        }
    });
    function afterAddCategory(result){
        var categoryName = result.name,
            categoryURL = result.href,
            newCategory = '<div class="col-md-3 col-md-offset-1 well oneCategory"><a href="'
        + categoryURL + '">' + categoryName + '</a></div>';
        $('.categoryList').append($(newCategory));
    }
    var categoryValidator = new Validator({name: $("#cat_name")});
    var addCategoryHandler = new DialogWithField(categoryValidator, addCategoryDialog, afterAddCategory, 'POST');

    $('.categories').on('click', 'button.add', function() {
        addCategoryHandler.dialog.dialog( "open" );
    });

    $('.categories').on('click', 'button.remove', function() {
        dialogDelete.dialog( "open" );
    });

    $('.categoryItems').on('click', 'button.add', function() {
        addItemHandler.dialog.dialog( "open" );
    });

    $('.categoryItems').on('click', 'button.remove', function() {
        dialogDelete.dialog( "open" );
    });

    $('.item').on('click', 'button.edit', function() {
        editItemHandler.dialog.dialog( "open" );
    });

    $('.item').on('click', 'button.delete', function() {
        dialogDelete.dialog( "open" );
    });
});
