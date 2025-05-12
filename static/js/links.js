document.addEventListener("DOMContentLoaded", () => {
    function displayEcommerceLinks(containerId, productName) {
        const ecommerceList = document.getElementById(containerId);
        if (!ecommerceList) return;

        // Clear previous content
        ecommerceList.innerHTML = '';

        // Header message
        const message = document.createElement("p");
        message.innerHTML = `Got it! Here are the best e-commerce websites where you can buy a <strong>${productName}</strong> online:`;
        ecommerceList.appendChild(message);

        // List of e-commerce links
        const ecommerceLinks = [
            { name: "Jumia", url: "https://www.jumia.com.ng/" },
            { name: "Konga", url: "https://www.konga.com/" },
            { name: "Slot", url: "https://slot.ng/" },
            { name: "Kara", url: "https://kara.com.ng/" },
            { name: "Jiji", url: "https://jiji.ng/" },
            { name: "Ajebo Market", url: "https://ajebomarket.com/" },
            { name: "Amazon", url: "https://www.amazon.com/" },
            { name: "Top Success", url: "https://topsuccess.ng/" },
            { name: "Temu", url: "https://www.temu.com/" }
        ];

        // Create a numbered list
        const list = document.createElement("ol");

        ecommerceLinks.forEach(link => {
            const listItem = document.createElement("li");
            const anchor = document.createElement("a");
            anchor.href = link.url;
            anchor.target = "_blank"; // Open in new tab
            anchor.textContent = link.name;
            listItem.appendChild(anchor);
            list.appendChild(listItem);
        });

        ecommerceList.appendChild(list);
        ecommerceList.style.display = "block"; // Show the list
    }

    // Example usage in chatbot (replace with actual integration logic)
    window.showEcommerceLinksInChat = (productName) => {
        displayEcommerceLinks("chat-ecommerce-list", productName);
    };

    // Example usage in voicebot (replace with actual integration logic)
    window.showEcommerceLinksInVoice = (productName) => {
        displayEcommerceLinks("voice-ecommerce-list", productName);
    };
});
