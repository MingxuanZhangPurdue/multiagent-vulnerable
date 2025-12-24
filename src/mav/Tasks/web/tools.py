"""
Web navigation tools for VisualWebArena-style web agent tasks.
Based on the WASP benchmark: https://github.com/facebookresearch/wasp
"""
from typing import Optional, Dict, Any, List
from mav.Tasks.web.environment import WebEnvironment


def _get_browser_and_page(env: WebEnvironment):
    return env.get_browser_env(), env.get_page()


def navigate_to_url(env: WebEnvironment, url: str) -> str:
    env.navigate_to(url)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            page.goto(url, wait_until="domcontentloaded")
            env.browser_state.current_url = page.url
            env.browser_state.page_title = page.title()
        except Exception as e:
            return f"Navigation failed: {e}"
    if env.attacker_domain in url:
        env.exfil_data.exfiltrated_data.append(url)
    return f"Successfully navigated to {url}"


def click(env: WebEnvironment, element_id: str) -> str:
    env.click_element(element_id)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            if element_id.startswith("[") and element_id.endswith("]"):
                elem_id = element_id.strip("[]")
                from mav.Tasks.web.visualwebarena.browser_env import create_click_action
                action = create_click_action(element_id=elem_id)
                browser_env.step(action)
            else:
                page.click(element_id)
        except Exception as e:
            return f"Click failed: {e}"
    return f"Clicked on element: {element_id}"


def type_text(env: WebEnvironment, element_id: str, text: str, clear_first: bool = True) -> str:
    env.type_text(element_id, text)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            if element_id.startswith("[") and element_id.endswith("]"):
                elem_id = element_id.strip("[]")
                from mav.Tasks.web.visualwebarena.browser_env import create_type_action
                action = create_type_action(element_id=elem_id, text=text)
                browser_env.step(action)
            else:
                if clear_first:
                    page.fill(element_id, text)
                else:
                    page.type(element_id, text)
        except Exception as e:
            return f"Type failed: {e}"
    action = "Cleared and typed" if clear_first else "Typed"
    return f"{action} '{text}' into element: {element_id}"


def scroll(env: WebEnvironment, direction: str, amount: int = 300) -> str:
    env.action_history.add_action("scroll", direction=direction, amount=amount)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_scroll_action
            action = create_scroll_action(direction=direction)
            browser_env.step(action)
        except Exception:
            if page is not None:
                scroll_map = {"down": f"window.scrollBy(0, {amount})", "up": f"window.scrollBy(0, -{amount})",
                              "right": f"window.scrollBy({amount}, 0)", "left": f"window.scrollBy(-{amount}, 0)"}
                page.evaluate(scroll_map.get(direction, ""))
    return f"Scrolled {direction} by {amount} pixels"


def go_back(env: WebEnvironment) -> str:
    env.action_history.add_action("go_back")
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_go_back_action
            action = create_go_back_action()
            browser_env.step(action)
        except Exception:
            if page is not None:
                page.go_back()
    return "Navigated back to previous page"


def go_forward(env: WebEnvironment) -> str:
    env.action_history.add_action("go_forward")
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None and page is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_go_forward_action
            action = create_go_forward_action()
            browser_env.step(action)
        except Exception:
            if page is not None:
                page.go_forward()
    return "Navigated forward"


def refresh_page(env: WebEnvironment) -> str:
    env.action_history.add_action("refresh")
    _, page = _get_browser_and_page(env)
    if page is not None:
        try:
            page.reload()
        except Exception as e:
            return f"Refresh failed: {e}"
    return f"Refreshed page: {env.browser_state.current_url}"


def get_page_content(env: WebEnvironment) -> str:
    browser_env, _ = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            obs = browser_env._get_obs()
            if "text" in obs:
                return obs["text"]
        except Exception:
            pass
    return env.browser_state.accessibility_tree or "Page content not available"


def get_current_url(env: WebEnvironment) -> str:
    _, page = _get_browser_and_page(env)
    if page is not None:
        try:
            return page.url
        except Exception:
            pass
    return env.browser_state.current_url


def submit_form(env: WebEnvironment, form_id: str, form_data: Dict[str, str]) -> str:
    env.submit_form(form_id, form_data)
    _, page = _get_browser_and_page(env)
    if page is not None:
        try:
            for field_name, field_value in form_data.items():
                try:
                    page.fill(f"{form_id} [name='{field_name}']", field_value)
                except Exception:
                    page.fill(f"[name='{field_name}']", field_value)
            page.click(f"{form_id} [type='submit']")
        except Exception as e:
            return f"Form submission failed: {e}"
    return f"Submitted form '{form_id}' with data: {form_data}"


def login(env: WebEnvironment, username: str, password: str) -> str:
    env.action_history.add_action("login", username=username)
    env.is_logged_in = True
    env.current_user = username
    return f"Successfully logged in as {username}"


def logout(env: WebEnvironment) -> str:
    env.action_history.add_action("logout", username=env.current_user)
    env.is_logged_in = False
    prev_user = env.current_user
    env.current_user = None
    return f"Successfully logged out from {prev_user}"


def open_new_url(env: WebEnvironment, url: str) -> str:
    env.action_history.add_action("open_new_url", url=url)
    env.navigate_to(url)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_new_tab_action, create_goto_url_action
            new_tab_action = create_new_tab_action()
            browser_env.step(new_tab_action)
            goto_action = create_goto_url_action(url=url)
            browser_env.step(goto_action)
        except Exception:
            if page is not None:
                page.evaluate(f"window.open('{url}', '_blank')")
    if env.attacker_domain in url:
        env.exfil_data.exfiltrated_data.append(url)
    return f"Opened new URL: {url}"


def execute_javascript(env: WebEnvironment, script: str) -> str:
    env.action_history.add_action("execute_js", script=script)
    _, page = _get_browser_and_page(env)
    result = None
    if page is not None:
        try:
            result = page.evaluate(script)
        except Exception as e:
            return f"JavaScript execution failed: {e}"
    return f"Executed JavaScript. Result: {result}"


def create_deploy_token(env: WebEnvironment, name: str, scopes: List[str]) -> Dict[str, str]:
    import secrets
    token = f"gldt-{secrets.token_hex(20)}"
    env.action_history.add_action("create_deploy_token", name=name, scopes=scopes)
    env.task_state.setdefault("deploy_tokens", []).append({"name": name, "token": token, "scopes": scopes})
    return {"name": name, "token": token, "scopes": scopes}


def create_post(env: WebEnvironment, title: str, content: str, subreddit: Optional[str] = None) -> Dict[str, Any]:
    import uuid
    post_id = str(uuid.uuid4())[:8]
    env.action_history.add_action("create_post", title=title, content=content, subreddit=subreddit)
    env.task_state.setdefault("posts", []).append({"id": post_id, "title": title, "content": content, "subreddit": subreddit})
    return {"id": post_id, "title": title, "url": f"/r/{subreddit}/comments/{post_id}"}


def send_message(env: WebEnvironment, recipient: str, message: str) -> Dict[str, Any]:
    env.action_history.add_action("send_message", recipient=recipient, message=message)
    env.task_state.setdefault("sent_messages", []).append({"recipient": recipient, "message": message})
    return {"status": "sent", "recipient": recipient}


def block_user(env: WebEnvironment, username: str) -> str:
    env.action_history.add_action("block_user", username=username)
    env.task_state.setdefault("blocked_users", []).append(username)
    return f"Blocked user: {username}"


def get_accessibility_tree(env: WebEnvironment) -> str:
    browser_env, _ = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            obs = browser_env._get_obs()
            if "text" in obs:
                env.browser_state.accessibility_tree = obs["text"]
                return obs["text"]
        except Exception:
            pass
    return env.browser_state.accessibility_tree


def take_screenshot(env: WebEnvironment) -> str:
    env.action_history.add_action("screenshot")
    _, page = _get_browser_and_page(env)
    if page is not None:
        try:
            import base64
            screenshot_bytes = page.screenshot()
            env.browser_state.screenshot_base64 = base64.b64encode(screenshot_bytes).decode()
        except Exception as e:
            return f"Screenshot failed: {e}"
    return f"Screenshot taken of {env.browser_state.current_url}"


def press_key(env: WebEnvironment, key: str) -> str:
    env.action_history.add_action("press_key", key=key)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_key_press_action
            action = create_key_press_action(key_comb=key)
            browser_env.step(action)
        except Exception:
            if page is not None:
                page.keyboard.press(key)
    return f"Pressed key: {key}"


def hover(env: WebEnvironment, element_id: str) -> str:
    env.action_history.add_action("hover", element_id=element_id)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_hover_action
            elem_id = element_id.strip("[]") if element_id.startswith("[") else element_id
            action = create_hover_action(element_id=elem_id)
            browser_env.step(action)
        except Exception:
            if page is not None:
                page.hover(element_id)
    return f"Hovering over element: {element_id}"


def select_option(env: WebEnvironment, element_id: str, option: str) -> str:
    env.action_history.add_action("select_option", element_id=element_id, option=option)
    browser_env, page = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_select_option_action
            elem_id = element_id.strip("[]") if element_id.startswith("[") else element_id
            action = create_select_option_action(element_id=elem_id, option=option)
            browser_env.step(action)
        except Exception:
            if page is not None:
                page.select_option(element_id, option)
    return f"Selected '{option}' from element: {element_id}"


def stop(env: WebEnvironment, answer: str = "") -> str:
    env.action_history.add_action("stop", answer=answer)
    browser_env, _ = _get_browser_and_page(env)
    if browser_env is not None:
        try:
            from mav.Tasks.web.visualwebarena.browser_env import create_stop_action
            action = create_stop_action(answer=answer)
            browser_env.step(action)
        except Exception:
            pass
    return f"Stopped with answer: {answer}" if answer else "Stopped"

