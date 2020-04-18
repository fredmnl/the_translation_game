
var pregunta = "";
var respuestas = null;
var next_pregunta = "";
var next_respuestas = null;
var buffer = "";
var result = false;

function loadWord(){

    // Asynchronously get the word that will be displayed on the next call
    $.ajax({
        url: '/api/getWord/',
        type: 'GET',
        dataType: 'json',
        success: function(json){
            next_pregunta = json["_word"];
            next_respuestas = json["_word_dict"]["translation_es"];
        }
    });

    // Display the word that was previously buffered
    pregunta = next_pregunta;
    respuestas = next_respuestas;
    if(pregunta.length > 0){
        $(".upper-span").text(pregunta);
        var el     = $(".upper-text"),  
            newone = el.clone(true);
        el.addClass("toRemove");
        el.before(newone);
        $(".toRemove").remove();
    }
};

function sendResult(word, result){
    $.ajax({
        url: '/api/postResult/?word=' + word + '&result=' + result,
        type: 'GET',
        dataType: 'json'
    });
};

function captureBackspace(event){
    if(event.which == 8){
        buffer = buffer.substring(0, buffer.length - 1);
        $(".lower-span").text(buffer);
    }
};

function captureKeyboard(event){
    if(event.which == 13){
        $(".lower-span").removeClass("init");
        if(respuestas !== null){ // This is unnecessary if no word has been loaded yet, we are still displaying the first screen
            result = false;
            // Check the buffer against all available translations for a match
            respuestas.forEach(function (item, index){
                let norm = item.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase(); // Delete accents and change to lowercase
                if (buffer.toLowerCase() === norm){
                    result = true;
                }
            });
            sendResult(pregunta, result);
            if(result){
                $(".info-text span").text("Correct ! Réponses possibles : " + respuestas.toString());
                //$(".info-text span").css('color', 'green');
                $(".info-text span").removeClass("incorrect");
            } else {
                $(".info-text span").text("Incorrect ! Réponses possibles : " + respuestas.toString());
                //$(".info-text span").css('color', 'red');
                $(".info-text span").addClass("incorrect");
            }
        }
        buffer = "";
        loadWord();
    }
    var c = String.fromCharCode(event.which);
    var b = c.replace(/[^a-z0-9-! ]/gi,''); // Only allowing a simple character set
    buffer = buffer + b;
    $(".lower-span").text(buffer);
};

$(document).ready(function(){
    $(document).keypress(captureKeyboard);
    $(document).keydown(captureBackspace);
    loadWord();
});

