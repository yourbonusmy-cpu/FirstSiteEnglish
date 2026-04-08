function getCookie(name) {
    let cookieValue = null
    if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";")
        for (let cookie of cookies) {
            cookie = cookie.trim()
            if (cookie.startsWith(name + "=")) {
                cookieValue = decodeURIComponent(cookie.slice(name.length + 1))
                break
            }
        }
    }
    return cookieValue
}

const csrftoken = getCookie("csrftoken")

document.addEventListener("DOMContentLoaded", () => {

    function bindForm(formId, errorId) {
        const form = document.getElementById(formId)
        if (!form) return

        form.addEventListener("submit", async e => {
            e.preventDefault()

            const response = await fetch(form.dataset.url, {
                method: "POST",
                body: new FormData(form),
                headers: {
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest"
                }
            })

            const data = await response.json()

            if (data.success) {
                location.reload()
            } else {
                document.getElementById(errorId).textContent = data.error
            }
        })
    }

    bindForm("loginTab", "loginError")
    bindForm("registerTab", "registerError")

    const logoutBtn = document.getElementById("logoutBtn")

    if (logoutBtn) {
        logoutBtn.addEventListener("click", async e => {
            e.preventDefault()

            const response = await fetch("/accounts/logout/ajax/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrftoken,
                    "X-Requested-With": "XMLHttpRequest"
                }
            })

            const data = await response.json()
            console.log(data)

            if (data.success) {
                location.reload()
            }
        })
    }


})
