import router from "./router";

const isLoggedIn = () => !!localStorage.getItem("token");

const logIn = (token, email) => {
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);
    window.dispatchEvent(new Event("logIn"));
    router.push({ name: "home" });
};

const logOut = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    window.dispatchEvent(new Event("logOut"));
    router.push({ name: "login" });
};

export { isLoggedIn, logIn, logOut };
