/**
 * CareerPath AI - Roadmap Interactive Logic
 * Cycle task status (Not Started -> In Progress -> Completed) directly on click
 */

async function cycleStatusDirectly(cardElement, taskRef) {
  // 1. تحديد الحالة الحالية للبطاقة
  let currentStatus = "not_started";
  if (cardElement.classList.contains("status-completed"))
    currentStatus = "completed";
  else if (cardElement.classList.contains("status-in_progress"))
    currentStatus = "in_progress";

  // 2. تحديد الحالة الجديدة بشكل دائري
  let newStatus = "in_progress";
  if (currentStatus === "in_progress") newStatus = "completed";
  if (currentStatus === "completed") newStatus = "not_started";

  // 3. تحديث الواجهة فوراً (Optimistic UI) لمنع التقطيع
  cardElement.classList.remove(
    "status-not_started",
    "status-in_progress",
    "status-completed",
  );
  cardElement.classList.add("status-" + newStatus);

  const checkEl = cardElement.querySelector(".task-check");
  if (checkEl) {
    checkEl.textContent =
      newStatus === "completed" ? "✓" : newStatus === "in_progress" ? "⟳" : "";
  }

  // 4. إرسال البيانات عبر Fetch API إلى الـ Backend
  try {
    const response = await fetch(UPDATE_TASK_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": CSRF_TOKEN,
      },
      body: JSON.stringify({ task_ref: taskRef, status: newStatus }),
    });

    const data = await response.json();

    if (data.success) {
      const labels = {
        completed: "✓ Marked complete successfully! ✨",
        in_progress: "⟳ Task is now In Progress",
        not_started: "Task reset to not started",
      };

      // استدعاء التنبيه المخصص إذا كان موجوداً
      if (typeof showToast === "function") {
        showToast(labels[newStatus] || "Updated successfully");
      }

      // تحديث الصفحة لضمان دقة أشرطة التقدم (Progress Bars) من السيرفر
      // يمكنك إزالة هذا السطر إذا كنت تفضل التحديث عبر JS فقط دون عمل Reload
      window.location.reload();
    } else {
      // إرجاع الواجهة للحالة القديمة في حال الفشل
      cardElement.classList.remove("status-" + newStatus);
      cardElement.classList.add("status-" + currentStatus);

      if (typeof showToast === "function") {
        showToast("❌ Failed to update: " + (data.error || "Server error"));
      }
    }
  } catch (error) {
    // إرجاع الواجهة للحالة القديمة في حال انقطاع الاتصال
    cardElement.classList.remove("status-" + newStatus);
    cardElement.classList.add("status-" + currentStatus);

    if (typeof showToast === "function") {
      showToast("❌ Error in saving — please check internet connection");
    }
  }
}
