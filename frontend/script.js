async function summarize() {
    const url = document.getElementById("videoUrl").value;
  
    const response = await fetch("http://127.0.0.1:5000/summarize", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ url })
    });
  
    const data = await response.json();
  
    if (data.error) {
      document.getElementById("title").innerText = "Error:";
      document.getElementById("summary").innerText = data.error;
    } else {
      document.getElementById("title").innerText = data.title;
      document.getElementById("summary").innerText = data.summary;
    }
  }
  