import QtQuick
import Quickshell
import qs.Commons
import qs.Ui

BarWidget {
    id: root
    moduleName: "io.github.uripg.tablet"
    implicitWidth:barSize
    implicitHeight:barSize
    readonly property string controller: Qt.resolvedUrl("scripts/tablet").toString().replace(/^file:\/\//, "")
    Text {
        anchors.centerIn:parent
        text:"󰓶"
        color:root.bar ? root.bar.barForeground : Color.foreground
        font.family:root.bar ? root.bar.fontFamily : "sans"
        font.pixelSize:20
    }
    MouseArea {
        anchors.fill:parent
        acceptedButtons:Qt.LeftButton | Qt.RightButton
        cursorShape:Qt.PointingHandCursor
        onClicked:mouse => Quickshell.execDetached([root.controller,mouse.button===Qt.RightButton ? "auto" : "toggle"])
    }
}
