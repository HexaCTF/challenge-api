
import pytest
from unittest.mock import MagicMock
from challenge_api.db.repository.userchallenge_status import UserChallengeStatusRepository
from challenge_api.db.models import UserChallengeStatus
from challenge_api.objects.usrchallenge import UChallengeStatus
from challenge_api.exceptions.service import InvalidInputValue
from unittest.mock import patch

@pytest.fixture
def fake_userchallenge_status():
    return UChallengeStatus(
        userchallenge_idx=1,
        port=8080,
        status="running"
    )

@pytest.fixture
def fake_empty_status():
    return UChallengeStatus(
        userchallenge_idx=1,
        status="None",
        port=8081
    )

@pytest.fixture
def fake_empty_port():
    return UChallengeStatus(
        userchallenge_idx=1,
        status="terminated",
        port=0
    )

@pytest.fixture
def mock_userchallenge_status():
    userchallenge_status = MagicMock()
    userchallenge_status.userchallenge_idx = 1
    userchallenge_status.port = 8080
    userchallenge_status.status = "running"
    return userchallenge_status

@pytest.fixture
def mock_userchallenge_status():
    userchallenge_status = MagicMock()
    userchallenge_status.userchallenge_idx = 1
    userchallenge_status.port = 8080
    userchallenge_status.status = "running"
    return userchallenge_status

class TestUserChallengeStatusRepository:
    def setup_method(self):
        self.mock_session = MagicMock()
        self.repo = UserChallengeStatusRepository(session=self.mock_session)
    
    def test_create_success(self, fake_userchallenge_status, mock_userchallenge_status):
        userchallenge_status = self.repo.create(fake_userchallenge_status)
        
        assert userchallenge_status is not None
        assert userchallenge_status.userChallenge_idx == mock_userchallenge_status.userchallenge_idx
        assert userchallenge_status.port == mock_userchallenge_status.port
        assert userchallenge_status.status == mock_userchallenge_status.status
        
        self.mock_session.add.assert_called_once_with(userchallenge_status)
        self.mock_session.commit.assert_called_once()
    
    def test_create_invalid_input(self):
        with pytest.raises(InvalidInputValue) as e:
            self.repo.create(1)
            
        assert "Invalid input error when creating userchallenge status" in str(e)
    
    def test_get_by_id_success(self, mock_userchallenge_status):
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = mock_userchallenge_status
        
        userchallenge_status = self.repo.get_by_id(1)
        
        assert userchallenge_status is not None
        assert userchallenge_status.userchallenge_idx == 1
        assert userchallenge_status.port == 8080
        assert userchallenge_status.status == "running"
        
        self.mock_session.query.return_value.filter_by.assert_called_once_with(idx=1)
        self.mock_session.query.return_value.filter_by.return_value.first.assert_called_once_with()
        
    def test_get_by_id_does_not_exist(self):
        self.mock_session.query.return_value.filter_by.return_value.first.return_value = None
        
        userchallenge_status = self.repo.get_by_id(1)
        
        assert userchallenge_status is None
        
    def test_first_success(self, mock_userchallenge_status):
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.return_value = mock_userchallenge_status
        
        userchallenge_status = self.repo.first(1)
        
        assert userchallenge_status is not None
        assert userchallenge_status.userchallenge_idx == 1
        assert userchallenge_status.port == 8080
        assert userchallenge_status.status == "running"
        
        self.mock_session.query.return_value.filter_by.assert_called_once_with(id_=1)
        self.mock_session.query.return_value.filter_by.return_value.order_by.return_value.first.assert_called_once_with()


    def test_update_port_success(self, mock_userchallenge_status, fake_empty_status):
        with patch.object(self.repo, 'get_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = mock_userchallenge_status
            
            userchallenge_status = self.repo.update(fake_empty_status)
            
            assert userchallenge_status is not None
            assert userchallenge_status.port == fake_empty_status.port
            assert userchallenge_status.status == mock_userchallenge_status.status

            mock_get_by_id.assert_called_once_with(id_ = fake_empty_status.userchallenge_idx)
            self.mock_session.update.assert_called_once_with(userchallenge_status)
            self.mock_session.commit.assert_called_once()
        
        
        
    def test_update_status_success(self, mock_userchallenge_status, fake_empty_port):
        with patch.object(self.repo, 'get_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = mock_userchallenge_status

            userchallenge_status = self.repo.update(fake_empty_port)

            assert userchallenge_status is not None
            assert userchallenge_status.status == fake_empty_port.status
            assert userchallenge_status.port == mock_userchallenge_status.port

            mock_get_by_id.assert_called_once_with(id_ = fake_empty_port.userchallenge_idx)
            self.mock_session.update.assert_called_once_with(userchallenge_status)
            self.mock_session.commit.assert_called_once()
        
        
    def test_update_UserChallengeStatus_success(self, mock_userchallenge_status, fake_empty_status):
        with patch.object(self.repo, 'get_by_id') as mock_get_by_id:
            mock_get_by_id.return_value = mock_userchallenge_status
            
            userchallenge_status = self.repo.update(fake_empty_status)
            
            assert userchallenge_status is not None
            assert userchallenge_status.status == fake_empty_status.status
            assert userchallenge_status.port == mock_userchallenge_status.port
            
            mock_get_by_id.assert_called_once_with(id_ = fake_empty_status.userchallenge_idx)
            self.mock_session.update.assert_called_once_with(userchallenge_status)
            self.mock_session.commit.assert_called_once()
    
    
    