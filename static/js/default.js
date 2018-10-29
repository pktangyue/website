$(function() {
  NProgress.configure({
    showSpinner: false
  });
  $(document).on("pjax:start", function() {
    NProgress.start();
  });
  $(document).on("pjax:end", function() {
    NProgress.done();
  });
  $(document).pjax("a", "#pjax-container", {
    fragment: "#pjax-container",
    timeout: 3000
  });
  $(document).on("click", "#more-link", function(e) {
    var $this = $(this);
    $.ajax({
      url: $this.data("url"),
      dataType: "html",
      success: function(response) {
        response = $("<div>").append($.parseHTML(response)).find("#pjax-container > *");
        $(".more-post").before("<hr class='my-5'/>").before(response).remove();
        $this.blur();
      }
    });
  });
});