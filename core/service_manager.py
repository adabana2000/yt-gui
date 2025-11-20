"""Service manager for coordinating application services"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass
import asyncio
from enum import Enum

from core.event_bus import event_bus
from utils.logger import logger


class ServiceStatus(Enum):
    """Service status enumeration"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class ServiceConfig:
    """Service configuration"""
    max_workers: int = 5
    retry_count: int = 3
    timeout: int = 300
    enabled: bool = True


class BaseService(ABC):
    """Base service class for all application services"""

    def __init__(self, config: ServiceConfig, name: str = None):
        """Initialize base service

        Args:
            config: Service configuration
            name: Service name
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.status = ServiceStatus.STOPPED
        self.event_bus = event_bus

    @abstractmethod
    async def start(self) -> None:
        """Start the service"""
        pass

    @abstractmethod
    async def stop(self) -> None:
        """Stop the service"""
        pass

    async def restart(self) -> None:
        """Restart the service"""
        logger.info(f"Restarting service: {self.name}")
        await self.stop()
        await asyncio.sleep(1)
        await self.start()

    def is_running(self) -> bool:
        """Check if service is running

        Returns:
            True if running
        """
        return self.status == ServiceStatus.RUNNING

    def emit_event(self, event_name: str, data: Any = None):
        """Emit event through event bus

        Args:
            event_name: Event name
            data: Event data
        """
        full_event_name = f"{self.name.lower()}:{event_name}"
        self.event_bus.emit(full_event_name, data)

    async def emit_event_async(self, event_name: str, data: Any = None):
        """Emit event asynchronously through event bus

        Args:
            event_name: Event name
            data: Event data
        """
        full_event_name = f"{self.name.lower()}:{event_name}"
        await self.event_bus.emit_async(full_event_name, data)


class ServiceManager:
    """Service manager for coordinating all application services"""

    def __init__(self):
        """Initialize service manager"""
        self.services: Dict[str, BaseService] = {}
        self.event_bus = event_bus
        self._running = False

    def register_service(self, name: str, service: BaseService) -> None:
        """Register a service

        Args:
            name: Service name
            service: Service instance
        """
        self.services[name] = service
        logger.info(f"Registered service: {name}")

    def unregister_service(self, name: str) -> None:
        """Unregister a service

        Args:
            name: Service name
        """
        if name in self.services:
            del self.services[name]
            logger.info(f"Unregistered service: {name}")

    def get_service(self, name: str) -> Optional[BaseService]:
        """Get a service by name

        Args:
            name: Service name

        Returns:
            Service instance or None
        """
        return self.services.get(name)

    async def start_all(self) -> None:
        """Start all registered services"""
        logger.info("Starting all services...")
        self._running = True

        start_tasks = []
        for name, service in self.services.items():
            if service.config.enabled:
                logger.info(f"Starting service: {name}")
                service.status = ServiceStatus.STARTING
                try:
                    start_tasks.append(self._start_service_safely(name, service))
                except Exception as e:
                    logger.error(f"Error starting service {name}: {e}")
                    service.status = ServiceStatus.ERROR

        # Wait for all services to start
        await asyncio.gather(*start_tasks, return_exceptions=True)

        logger.info("All services started successfully")

    async def _start_service_safely(self, name: str, service: BaseService):
        """Start a service with error handling

        Args:
            name: Service name
            service: Service instance
        """
        try:
            await service.start()
            service.status = ServiceStatus.RUNNING
            logger.info(f"Service {name} started successfully")
        except Exception as e:
            logger.error(f"Failed to start service {name}: {e}")
            service.status = ServiceStatus.ERROR
            raise

    async def stop_all(self) -> None:
        """Stop all registered services"""
        logger.info("Stopping all services...")
        self._running = False

        stop_tasks = []
        for name, service in self.services.items():
            if service.is_running():
                logger.info(f"Stopping service: {name}")
                service.status = ServiceStatus.STOPPING
                try:
                    stop_tasks.append(self._stop_service_safely(name, service))
                except Exception as e:
                    logger.error(f"Error stopping service {name}: {e}")

        # Wait for all services to stop
        await asyncio.gather(*stop_tasks, return_exceptions=True)

        logger.info("All services stopped successfully")

    async def _stop_service_safely(self, name: str, service: BaseService):
        """Stop a service with error handling

        Args:
            name: Service name
            service: Service instance
        """
        try:
            await service.stop()
            service.status = ServiceStatus.STOPPED
            logger.info(f"Service {name} stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop service {name}: {e}")
            raise

    async def restart_service(self, name: str) -> bool:
        """Restart a specific service

        Args:
            name: Service name

        Returns:
            True if successful
        """
        service = self.services.get(name)
        if not service:
            logger.error(f"Service not found: {name}")
            return False

        try:
            await service.restart()
            return True
        except Exception as e:
            logger.error(f"Failed to restart service {name}: {e}")
            return False

    def get_service_status(self, name: Optional[str] = None) -> Dict[str, str]:
        """Get service status

        Args:
            name: Service name (None for all services)

        Returns:
            Dictionary of service statuses
        """
        if name:
            service = self.services.get(name)
            if service:
                return {name: service.status.value}
            return {name: "not_found"}

        return {
            name: service.status.value
            for name, service in self.services.items()
        }

    def is_all_running(self) -> bool:
        """Check if all services are running

        Returns:
            True if all services are running
        """
        return all(
            service.is_running()
            for service in self.services.values()
            if service.config.enabled
        )


# Global service manager instance
service_manager = ServiceManager()
