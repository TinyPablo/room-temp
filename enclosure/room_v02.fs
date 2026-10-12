FeatureScript 3095;
import(path : "onshape/std/common.fs", version : "3095.0");

function roomBox(context is Context, id is Id, a is Vector, b is Vector) returns Query
{
    fCuboid(context, id, { "corner1" : a * millimeter, "corner2" : b * millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function roomCylinder(context is Context, id is Id, x is number, y is number, z is number, h is number, diameter is number) returns Query
{
    fCylinder(context, id, { "bottomCenter" : vector(x,y,z)*millimeter,
        "topCenter" : vector(x,y,z+h)*millimeter, "radius" : diameter/2*millimeter });
    return qCreatedBy(id, EntityType.BODY);
}
function roomCut(context is Context, id is Id, target is Query, tool is Query)
{
    opBoolean(context, id, { "tools" : tool, "targets" : target, "operationType" : BooleanOperationType.SUBTRACTION });
}
function roomJoin(context is Context, id is Id, target is Query, tool is Query)
{
    opBoolean(context, id, { "tools" : qUnion([target,tool]), "operationType" : BooleanOperationType.UNION });
}
function roomNamePart(context is Context, part is Query, title is string)
{
    setProperty(context, { "entities" : part, "propertyType" : PropertyType.NAME, "value" : title });
}
function roomRoundedBox(context is Context, id is Id, a is Vector, b is Vector, radius is number) returns Query
{
    const part = roomBox(context, id+"solid", a, b);
    var corners = [];
    for (var x in [a[0],b[0]])
        for (var y in [a[1],b[1]])
            corners = append(corners, qContainsPoint(qOwnedByBody(part,EntityType.EDGE), vector(x,y,(a[2]+b[2])/2)*millimeter));
    opFillet(context,id+"corners", { "entities" : qUnion(corners), "radius" : radius*millimeter });
    return part;
}
function roomInsertBore(context is Context, id is Id, part is Query, x is number, y is number, top is number, diameter is number)
{
    roomCut(context,id+"cut",part,roomCylinder(context,id+"tool",x,y,top-4.5,5.5,diameter));
}

annotation { "Feature Type Name" : "RoomEnclosureV02" }
export const roomV02 = defineFeature(function(context is Context, id is Id, definition is map)
precondition
{
    annotation { "Name" : "Assembly view (disable for printing)" }
    definition.assembled is boolean;
    annotation { "Name" : "Insert bore diameter" }
    isLength(definition.insertDiameter, { (millimeter) : [3.0,3.1,3.4] } as LengthBoundSpec);
    annotation { "Name" : "Sensor PCB thickness" }
    isLength(definition.sensorPcbThickness, { (millimeter) : [1.4,1.5,1.6] } as LengthBoundSpec);
}
{
    const bore = definition.insertDiameter / millimeter;
    const sensorTop = 10 + definition.sensorPcbThickness / millimeter;
    if (4 - (sensorTop - 10) < 2.4)
        throw "Insufficient sensor screw engagement";
    // Print coordinates: shell open upwards; invert the assembled unit for shelf use.
    const shell = roomRoundedBox(context,id+"shell",vector(0,0,0),vector(88,62,34),7);
    opFillet(context,id+"outerTop", {
        "entities" : qContainsPoint(qOwnedByBody(shell,EntityType.EDGE), vector(44,0,0)*millimeter),
        "radius" : 1.2*millimeter,
        "tangentPropagation" : true
    });
    const cavity = roomRoundedBox(context,id+"cavity",vector(2.4,2.4,2.4),vector(85.6,59.6,35),4.6);
    roomCut(context,id+"hollow",shell,cavity);

    const caseMounts = [vector(7,7),vector(81,7),vector(7,55),vector(81,55)];
    for (var i=0; i<4; i+=1)
    {
        const p=caseMounts[i];
        const station=id+("caseMount"~i);
        roomJoin(context,station+"join",shell,roomCylinder(context,station+"boss",p[0],p[1],2,32,8));
        roomInsertBore(context,station+"insert",shell,p[0],p[1],34,bore);
    }

    // Pico: 51 x 21 mm, hole spacing 47 x 11.4 mm, USB at x=4, antenna at x=55.
    const picoMounts = [vector(6,16.8),vector(6,28.2),vector(53,16.8),vector(53,28.2)];
    for (var i=0; i<4; i+=1)
    {
        const p=picoMounts[i];
        const station=id+("picoMount"~i);
        roomJoin(context,station+"join",shell,roomCylinder(context,station+"boss",p[0],p[1],2,6,5.3));
        roomInsertBore(context,station+"insert",shell,p[0],p[1],8,bore);
    }
    // Oversized plug opening; verify against the actual microUSB cable moulding.
    const usb = roomBox(context,id+"usbTool",vector(-1,15,5),vector(2.6,30,15));
    roomCut(context,id+"usbCut",shell,usb);

    // Thermal baffle stops short of the antenna side; a top notch routes jumpers.
    roomJoin(context,id+"baffleJoin",shell,roomBox(context,id+"baffle",vector(2.3,36,2),vector(66,37.6,32)));
    roomCut(context,id+"wireNotchCut",shell,roomBox(context,id+"wireNotch",vector(18,35,17),vector(30,38.6,35)));

    // Drop-in PCB: x=25..37, y=44..56. Headers face +X into the open bay.
    // Hole centres are 1.5 mm from the edges, 9 mm apart; PCB rests at z=10.
    const sensorMounts = [vector(26.5,45.5),vector(26.5,54.5)];
    for (var i=0; i<2; i+=1)
    {
        const p=sensorMounts[i];
        const station=id+("sensorMount"~i);
        roomJoin(context,station+"join",shell,roomCylinder(context,station+"boss",p[0],p[1],2,8,5.3));
        roomInsertBore(context,station+"insert",shell,p[0],p[1],10,bore);
    }

    // Narrow bridges print without internal support and expose the sensor bay to air.
    for (var i=0; i<10; i+=1)
    {
        const station=id+("vent"~i);
        const x=16+i*4.6;
        roomCut(context,station+"cut",shell,roomBox(context,station+"tool",vector(x,59,7),vector(x+2.4,63,24)));
    }
    for (var i=0; i<4; i+=1)
    {
        const station=id+("rearVent"~i);
        roomCut(context,station+"cut",shell,roomBox(context,station+"tool",vector(65+i*4, -1, 8),vector(67.4+i*4,3,20)));
    }
    roomNamePart(context,shell,"ROOM V02 - shell 88 x 62 x 34 - PETG");

    // Bottom cover, external face on the bed. 1.5 mm remains under each screw head.
    const dx=100;
    const lid=roomRoundedBox(context,id+"lid",vector(dx,0,0),vector(dx+88,62,4),7);
    opFillet(context,id+"lidOuterRim", {
        "entities" : qContainsPoint(qOwnedByBody(lid,EntityType.EDGE),vector(dx+44,0,0)*millimeter),
        "radius" : 1.0*millimeter, "tangentPropagation" : true
    });
    // Short locating tabs avoid the corner bosses and sensor rails.
    for (var y in [2.7,57.8])
        roomJoin(context,id+("tabJoin"~y),lid,roomBox(context,id+("tab"~y),vector(dx+38,y,3.8),vector(dx+50,y+1.5,5.5)));
    for (var i=0; i<4; i+=1)
    {
        const p=caseMounts[i];
        const station=id+("lidScrew"~i);
        roomCut(context,station+"throughCut",lid,roomCylinder(context,station+"through",dx+p[0],p[1],-1,7,2.3));
        roomCut(context,station+"headCut",lid,roomCylinder(context,station+"head",dx+p[0],p[1],-1,3.5,3.8));
    }
    roomNamePart(context,lid,"ROOM V02 - bottom cover - M2 x 4");

    // Swept envelopes check vertical insertion, not just the final board position.
    const picoGauge=roomBox(context,id+"picoGauge",vector(4.1,12.1,8.05),vector(54.9,32.9,8.95));
    const sensorSweep=roomBox(context,id+"sensorSweep",vector(25,44,10.01),vector(37,56,40));
    // Reserve 25 mm beyond the PCB edge for bent headers and female connectors.
    const connectorSweep=roomBox(context,id+"connectorSweep",vector(33,44,7),vector(62,56,40));
    var gauges=[picoGauge,sensorSweep,connectorSweep];
    for (var i=0; i<2; i+=1)
    {
        const p=sensorMounts[i];
        gauges=append(gauges,roomCylinder(context,id+("driverGauge"~i),p[0],p[1],10.01,30,6));
    }
    if (size(evCollision(context,{"tools":qUnion(gauges),"targets":shell}))!=0)
        throw "A board insertion path, connector envelope or screwdriver path is obstructed";
    opDeleteBodies(context,id+"deleteGauges",{"entities":qUnion(gauges)});
    if (definition.assembled)
    {
        opTransform(context,id+"shellAssembly",{
            "bodies":shell,
            "transform":rotationAround(line(vector(0,31,19)*millimeter,vector(1,0,0)),180*degree)
        });
        opTransform(context,id+"lidAssembly",{
            "bodies":lid,"transform":transform(vector(-100,0,0)*millimeter)
        });
        for (var pair in [[lid,shell]])
            for (var clash in evCollision(context,{"tools":pair[0],"targets":pair[1]}))
                if (clash["type"] != ClashType.ABUT_NO_CLASS)
                    throw "Printed parts overlap in the assembly";
    }
    for (var part in [shell,lid])
        if (size(evaluateQuery(context,part))!=1 || evVolume(context,{"entities":part})<=0*millimeter^3)
            throw "Each printed part must be one connected solid";
}, { "assembled" : false, "insertDiameter" : 3.1*millimeter, "sensorPcbThickness" : 1.5*millimeter });
