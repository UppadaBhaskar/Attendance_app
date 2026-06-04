function confirmDelete(studentName) {
  return confirm('Delete student "' + studentName + '"? This cannot be undone.');
}

function markAll(status) {
  var form = document.getElementById('attendance-form');
  if (!form) return;
  form.querySelectorAll('input[type=radio][value="' + status + '"]').forEach(function(radio) {
    radio.checked = true;
    var label = radio.closest('.mark-btn');
    if (label) {
      label.parentElement.querySelectorAll('.mark-btn').forEach(function(b) {
        b.classList.remove('active');
      });
      label.classList.add('active');
    }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.mark-btn input').forEach(function(input) {
    input.addEventListener('change', function() {
      var group = input.closest('.mark-buttons');
      if (!group) return;
      group.querySelectorAll('.mark-btn').forEach(function(b) { b.classList.remove('active'); });
      input.closest('.mark-btn').classList.add('active');
    });
  });
});
