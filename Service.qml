import QtQuick
import Quickshell
import Quickshell.Io
import "ui"

Item {
    id: service
    property var shell: null
    property var manifest: null
    readonly property string controller: Qt.resolvedUrl("scripts/tablet").toString().replace(/^file:\/\//, "")
    property bool stopping: false
    function toggle() { ui.control("toggle") }
    function showControls() { ui.expanded=true; ui.control("on") }
    Process {
        id: controllerProcess
        command: [Qt.resolvedUrl("scripts/start-service").toString().replace(/^file:\/\//, "")]
        running: true
        onExited: if (!service.stopping) restartTimer.restart()
        stderr: SplitParser { onRead: data => console.warn("Tablet Mode: "+data) }
    }
    Timer { id:restartTimer; interval:3000; onTriggered:controllerProcess.running=true }
    TabletUi { id:ui; controller:service.controller }
    Component.onDestruction: {
        service.stopping=true
        Quickshell.execDetached(["systemctl", "--user", "stop", "omarchy-tablet-plugin.service"])
    }
}
