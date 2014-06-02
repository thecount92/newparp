var current_mode;

function chatsUpdate(first) {    
    if ($('body').prop('class')) {
        mode = $('body').prop('class');
    } else {
        mode = 'none';
    }
    
    if (current_mode == mode || first) {
        $('#under-page').empty();
        if ($('body.mobile').length>0) {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            for(chat in chats) {
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-').replace(/\//g,'-'));
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
                console.log(chat);
            }
        } else if ($('body.nobile').length>0) {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=2) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=1; i<chats.length; i+=2) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-2');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                console.log();
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
        } else {
            $('<div>').addClass('section').prop('id', 'column-1').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-2').appendTo('#under-page');
            $('<div>').addClass('section').prop('id', 'column-3').appendTo('#under-page');
            for (var i=0; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-1');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=1; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-2');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
            for (var i=2; i<chats.length; i+=3) {
                chat = chats[i];
                $('<div>').addClass('card chat').prop('id', 'chat-'+chat.url.replace(/\//g,'-')).appendTo('#column-3');
                $('<a>').addClass('title').prop('href','/'+chat.url).text(chat.title+(chat.unread ? ' '+chat.url : '')).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                if (chat.type == 'group') {
                    $('<div>').addClass('topic').text(chat.topic).appendTo('#chat-'+chat.url.replace(/\//g,'-'));
                }
            }
        }
    }
    current_mode = mode;
}

$(function(){
    screenCheck();

    if ($('body').prop('class')) {
        current_mode = $('body').prop('class');
    } else {
        current_mode = 'none';
    }
    
    chatsUpdate(true);
});

$(window).resize(function () {
    screenCheck();
    chatsUpdate();
});