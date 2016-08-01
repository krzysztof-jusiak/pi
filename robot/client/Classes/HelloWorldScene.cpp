#include "HelloWorldScene.h"
#include "SimpleAudioEngine.h"
#include "2d/CCDrawingPrimitives.h"

USING_NS_CC;

Scene* HelloWorld::createScene()
{
    // 'scene' is an autorelease object
    auto scene = Scene::create();
    
    // 'layer' is an autorelease object
    auto layer = HelloWorld::create();

    // add layer as a child to scene
    scene->addChild(layer);

    // return the scene
    return scene;
}

// on "init" you need to initialize your instance
bool HelloWorld::init()
{
    //////////////////////////////
    // 1. super init first
    if ( !Layer::init() )
    {
        return false;
    }

    Size visibleSize = Director::getInstance()->getVisibleSize();
    Vec2 origin = Director::getInstance()->getVisibleOrigin();

    webView = cocos2d::experimental::ui::WebView::create();

    webView->setAnchorPoint(Point(0.f, 0.0f)); // top left
    webView->setContentSize(Size(visibleSize.width, visibleSize.height));
    webView->setPosition(Vec2(0.f, 25.f));
    //webView->loadURL("http://192.168.1.71:10088/?action=stream");
    webView->loadFile("index.html");
    webView->setScalesPageToFit(true);
    CCLOG("%f %f", visibleSize.width, visibleSize.height); // 640 x 360

    //node = DrawNode::create();
    Device::setAccelerometerEnabled(true);

    auto listener = EventListenerAcceleration::create([&](Acceleration* acc, Event* event){
      //node->clear();
      //node->drawLine(Vec2(100, 150 + (acc->x / 2. * 250.f)), Vec2(400, 150 - (acc->x / 2. * 250.f)), Color4F(1.0, 1.0, 1.0, 1.0));
      std::stringstream str;
      str << "drawLine(50, " << 250 - (acc->x / 2. * 250.f) << ", 100, " << 250 + (acc->x / 2. * 250.f) << ");";
      log("JS: %s", str.str().c_str());
      webView->evaluateJS(str.str());
        } );
    _eventDispatcher->addEventListenerWithSceneGraphPriority(listener, this);

    this->addChild(webView, 1);
    //this->addChild(node, 1000);


    return true;
}


void HelloWorld::menuCloseCallback(Ref* pSender)
{
    //Close the cocos2d-x game scene and quit the application
    Director::getInstance()->end();

    #if (CC_TARGET_PLATFORM == CC_PLATFORM_IOS)
    exit(0);
#endif
    
    /*To navigate back to native iOS screen(if present) without quitting the application  ,do not use Director::getInstance()->end() and exit(0) as given above,instead trigger a custom event created in RootViewController.mm as below*/
    
    //EventCustom customEndEvent("game_scene_close_event");
    //_eventDispatcher->dispatchEvent(&customEndEvent);
    
    
}
