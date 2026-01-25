import pytest
from dataclasses import dataclass
from pydantic import BaseModel

from R5.http import Http
from R5.http.http import HttpConfig
from R5.ioc import Container


class JSONPlaceholderUser(BaseModel):
    id: int
    name: str
    email: str
    username: str


class JSONPlaceholderPost(BaseModel):
    userId: int
    id: int
    title: str
    body: str


@dataclass
class UserDataclass:
    id: int
    name: str
    email: str
    username: str


@pytest.fixture
async def http_client():
    """Cliente HTTP para tests de integración."""
    config = HttpConfig()
    config.connect_timeout = 10.0
    config.read_timeout = 10.0
    async with Http(config) as client:
        yield client


@pytest.mark.integration
class TestHttpGetIntegration:
    """Tests de integración para GET requests."""
    
    @pytest.mark.asyncio
    async def test_get_user_pydantic(self, http_client):
        """Test GET con mapeo a Pydantic model."""
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/1")
        user = result.to(JSONPlaceholderUser)
        
        assert user is not None
        assert user.id == 1
        assert user.name is not None
        assert "@" in user.email
        assert result.status == 200
        assert result.exception is None
    
    @pytest.mark.asyncio
    async def test_get_user_dataclass(self, http_client):
        """Test GET con mapeo a dataclass."""
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/1")
        user = result.to(UserDataclass)
        
        assert user is not None
        assert user.id == 1
        assert user.name is not None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_get_user_dict(self, http_client):
        """Test GET con mapeo a dict."""
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/1")
        data = result.to(dict)
        
        assert data is not None
        assert data["id"] == 1
        assert "name" in data
        assert "email" in data
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_get_users_list(self, http_client):
        """Test GET con mapeo a lista."""
        result = await http_client.get("https://jsonplaceholder.typicode.com/users")
        users = result.to(list)
        
        assert users is not None
        assert len(users) > 0
        assert isinstance(users, list)
        assert users[0]["id"] is not None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_get_with_query_params(self, http_client):
        """Test GET con query parameters."""
        result = await http_client.get(
            "https://jsonplaceholder.typicode.com/posts",
            params={"userId": 1}
        )
        posts = result.to(list)
        
        assert posts is not None
        assert len(posts) > 0
        for post in posts:
            assert post["userId"] == 1
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_get_404_not_found(self, http_client):
        """Test GET que retorna 404."""
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/99999")
        
        assert result.status == 404
        assert result.response is not None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpPostIntegration:
    """Tests de integración para POST requests."""
    
    @pytest.mark.asyncio
    async def test_post_json(self, http_client):
        """Test POST con JSON."""
        new_post = {
            "title": "Integration Test Post",
            "body": "This is a test post from R5 Http client",
            "userId": 1
        }
        
        result = await http_client.post(
            "https://jsonplaceholder.typicode.com/posts",
            json=new_post
        )
        
        assert result.status == 201
        post = result.to(JSONPlaceholderPost)
        
        assert post is not None
        assert post.title == new_post["title"]
        assert post.body == new_post["body"]
        assert post.userId == new_post["userId"]
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_post_form_data(self, http_client):
        """Test POST con form data."""
        form_data = {
            "title": "Form Test",
            "body": "Body text",
            "userId": 1
        }
        
        result = await http_client.post(
            "https://jsonplaceholder.typicode.com/posts",
            data=form_data
        )
        
        assert result.status == 201
        assert result.exception is None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpPutIntegration:
    """Tests de integración para PUT requests."""
    
    @pytest.mark.asyncio
    async def test_put_update(self, http_client):
        """Test PUT para actualizar recurso."""
        updated_post = {
            "id": 1,
            "title": "Updated Title",
            "body": "Updated body content",
            "userId": 1
        }
        
        result = await http_client.put(
            "https://jsonplaceholder.typicode.com/posts/1",
            json=updated_post
        )
        
        assert result.status == 200
        post = result.to(JSONPlaceholderPost)
        
        assert post is not None
        assert post.id == 1
        
        await http_client.close()


@pytest.mark.integration
class TestHttpDeleteIntegration:
    """Tests de integración para DELETE requests."""
    
    @pytest.mark.asyncio
    async def test_delete_resource(self, http_client):
        """Test DELETE."""
        result = await http_client.delete(
            "https://jsonplaceholder.typicode.com/posts/1"
        )
        
        assert result.status == 200
        assert result.exception is None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpPatchIntegration:
    """Tests de integración para PATCH requests."""
    
    @pytest.mark.asyncio
    async def test_patch_partial_update(self, http_client):
        """Test PATCH para actualización parcial."""
        partial_update = {
            "title": "Patched Title"
        }
        
        result = await http_client.patch(
            "https://jsonplaceholder.typicode.com/posts/1",
            json=partial_update
        )
        
        assert result.status == 200
        post = result.to(dict)
        
        assert post is not None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpHandlers:
    """Tests de integración para handlers."""
    
    @pytest.mark.asyncio
    async def test_on_status_handler(self, http_client):
        """Test handler on_status."""
        handler_calls = []
        
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/1")
        
        user = (result
            .on_status(200, lambda req, res: handler_calls.append("200_OK"))
            .on_status(404, lambda req, res: handler_calls.append("404_NOT_FOUND"))
            .to(JSONPlaceholderUser))
        
        assert user is not None
        assert "200_OK" in handler_calls
        assert "404_NOT_FOUND" not in handler_calls
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_on_exception_handler(self, http_client):
        """Test handler on_exception con dominio inválido."""
        handler_calls = []
        
        result = await http_client.get("https://this-domain-does-not-exist-12345.com")
        
        result.on_exception(lambda e: handler_calls.append(type(e).__name__))
        
        assert len(handler_calls) > 0
        assert result.exception is not None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_chaining_handlers(self, http_client):
        """Test chaining completo de handlers."""
        calls = []
        
        result = await http_client.get("https://jsonplaceholder.typicode.com/users/999")
        
        user = (result
            .on_status(404, lambda req, res: calls.append("not_found"))
            .on_status(200, lambda req, res: calls.append("success"))
            .on_exception(lambda e: calls.append("error"))
            .to(JSONPlaceholderUser))
        
        assert "not_found" in calls
        assert user is None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpTimeouts:
    """Tests de integración para timeouts."""
    
    @pytest.mark.asyncio
    async def test_custom_timeout(self, http_client):
        """Test con timeout personalizado."""
        result = await http_client.get(
            "https://jsonplaceholder.typicode.com/users/1",
            timeout=15.0
        )
        
        assert result.status == 200
        assert result.exception is None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_timeout_on_slow_endpoint(self, http_client):
        """Test timeout en endpoint lento."""
        result = await http_client.get(
            "https://httpbin.org/delay/10",
            timeout=2.0
        )
        
        assert result.exception is not None
        
        await http_client.close()


@pytest.mark.integration
class TestHttpHeaders:
    """Tests de integración para headers."""
    
    @pytest.mark.asyncio
    async def test_custom_headers(self, http_client):
        """Test con headers personalizados."""
        custom_headers = {
            "Accept": "application/json",
            "X-Custom-Header": "R5-Test"
        }
        
        result = await http_client.get(
            "https://httpbin.org/headers",
            headers=custom_headers
        )
        
        assert result.status == 200
        data = result.to(dict)
        
        assert data is not None
        headers = data.get("headers", {})
        assert "X-Custom-Header" in headers
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_user_agent_header(self, http_client):
        """Test User-Agent por defecto."""
        result = await http_client.get("https://httpbin.org/user-agent")
        
        assert result.status == 200
        data = result.to(dict)
        
        assert data is not None
        assert "R5-HttpClient" in data.get("user-agent", "")
        
        await http_client.close()


@pytest.mark.integration
class TestHttpRedirects:
    """Tests de integración para redirecciones."""
    
    @pytest.mark.asyncio
    async def test_follow_redirects_default(self, http_client):
        """Test seguir redirecciones por defecto."""
        result = await http_client.get("https://httpbin.org/redirect/1")
        
        assert result.status == 200
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_no_follow_redirects(self, http_client):
        """Test sin seguir redirecciones."""
        result = await http_client.get(
            "https://httpbin.org/redirect/1",
            follow_redirects=False
        )
        
        assert result.status in (301, 302, 303, 307, 308)
        
        await http_client.close()


@pytest.mark.integration
class TestHttpErrorHandling:
    """Tests de integración para manejo de errores."""
    
    @pytest.mark.asyncio
    async def test_network_error(self, http_client):
        """Test error de red con dominio inválido."""
        result = await http_client.get("https://invalid-domain-12345-xyz.com")
        
        assert result.exception is not None
        assert result.status == 0
        assert result.response is None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_500_server_error(self, http_client):
        """Test error 500 del servidor."""
        result = await http_client.get("https://httpbin.org/status/500")
        
        assert result.status == 500
        assert result.response is not None
        assert result.exception is None
        
        await http_client.close()
    
    @pytest.mark.asyncio
    async def test_multiple_status_codes(self, http_client):
        """Test múltiples códigos de estado."""
        test_cases = [
            ("https://httpbin.org/status/200", 200),
            ("https://httpbin.org/status/201", 201),
            ("https://httpbin.org/status/400", 400),
            ("https://httpbin.org/status/404", 404),
            ("https://httpbin.org/status/503", 503),
        ]
        
        for url, expected_status in test_cases:
            result = await http_client.get(url)
            assert result.status == expected_status, f"Failed for {url}"
        
        await http_client.close()


@pytest.mark.integration
class TestHttpWithIoC:
    """Tests de integración con IoC container."""
    
    @pytest.mark.asyncio
    async def test_http_resource_from_container(self):
        """Test Http como resource desde container."""
        container = Container()
        
        async with await container.resolve(Http) as http:
            result = await http.get("https://jsonplaceholder.typicode.com/users/1")
            user = result.to(dict)
            
            assert user is not None
            assert isinstance(user, dict)
            assert "id" in user
