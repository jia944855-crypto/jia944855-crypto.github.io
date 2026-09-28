jQuery(document).ready(function(){

    jQuery('.single-slider-no-text').slick({
        arrows: false,
        dots: true,
        loop: false,
        adaptiveHeight: true,
        infinite: false,
        slidesToScroll: 1
 
    });

 

    var single_no_text_scrollTop_init = jQuery(window).scrollTop(); // Current scroll position
    var single_no_text_windowHeight_init = jQuery(window).height(); // Height of the window
    var single_no_text_divOffset_init = jQuery('.single-slider-no-text-wrapper').offset().top; // Top offset of the div
 

    // Check if the div is in the viewport
    if (single_no_text_scrollTop_init + single_no_text_windowHeight_init > single_no_text_divOffset_init) {
        jQuery('.single-slider-no-text-wrapper').addClass('opacity-1'); // Fade in the div
    }

 

    jQuery(window).on('scroll', function() {
        // console.log('scrolling');
        var single_no_text_scrollTop = jQuery(this).scrollTop(); // Current scroll position
        var single_no_text_windowHeight = jQuery(this).height(); // Height of the window
        var single_no_text_divOffset = jQuery('.single-slider-no-text-wrapper').offset().top; // Top offset of the div

        // Check if the div is in the viewport
        if (single_no_text_scrollTop + single_no_text_windowHeight > single_no_text_divOffset) {
            jQuery('.single-slider-no-text-wrapper').addClass('opacity-1'); // Fade in the div
        }

 
    });

});

